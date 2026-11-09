"""Casos de uso dos recursos básicos, sem dependência de Flask ou SQLAlchemy."""
from dataclasses import asdict, fields
from datetime import datetime, timezone
from uuid import uuid4
import json
import re
from prismati.domain.services.maturity_calculator import MaturityCalculator
from prismati.application.ports.catalog import Catalog
from prismati.domain.entities.company import Company
from prismati.domain.entities.user import User
from prismati.domain.entities.company_membership import CompanyMembership
from prismati.domain.entities.questionnaire import Questionnaire, QuestionnaireVersion
from prismati.domain.entities.dimension import Dimension
from prismati.domain.entities.question import Question, Alternative
from prismati.domain.entities.assessment import Assessment
from prismati.domain.entities.answer import Answer
from prismati.domain.exceptions.domain_exceptions import ForbiddenError, NotFoundError, ValidationError, ConflictError

CNPJ_PATTERN = r'[.\\/-]*(?:[A-Za-z0-9][.\\/-]*){12}(?:[0-9][.\\/-]*){2}'


def normalize_cnpj(value):
    if not isinstance(value, str) or not re.fullmatch(CNPJ_PATTERN, value):
        raise ValidationError('CNPJ deve conter 14 caracteres: letras ou números nas primeiras 12 posições e números nas duas últimas. Pontos, barras e hífens são removidos.')
    return re.sub(r'[.\\/-]', '', value).upper()


ENTITIES = dict(companies=Company, users=User, memberships=CompanyMembership,
                questionnaires=Questionnaire, versions=QuestionnaireVersion,
                dimensions=Dimension, questions=Question, alternatives=Alternative,
                assessments=Assessment, answers=Answer)
EDITABLE = {
 'companies': {'razao_social','cnpj','segmento','porte','status'},
 'users': {'nome','email','senha','role','status'},
 'memberships': {'empresa_id','usuario_id'},
 'questionnaires': {'nome','descricao'},
 'versions': {'questionario_id','versao','versao_metodologia'},
 'dimensions': {'versao_questionario_id','nome','descricao','ordem','codigo'},
 'questions': {'dimensao_id','texto','ordem','codigo','explicacao','orientacao_evidencia'},
 'alternatives': {'pergunta_id','descricao','pontuacao','ordem'},
 'assessments': {'empresa_id','versao_questionario_id'},
 'answers': {'avaliacao_id','pergunta_id','tipo_resposta','alternativa_id','justificativa'},
}

class CatalogService:
    def __init__(self, repo: Catalog, hash_password):
        self.repo = repo
        self.hash_password = hash_password

    def require(self, resource, identifier, lock=False):
        row = self.repo.get(resource, identifier, lock)
        if row is None:
            raise NotFoundError(resource, identifier)
        return row

    def company(self, actor):
        links = self.repo.list('memberships', {'usuario_id': actor['id']})
        return links[0]['empresa_id'] if links else None

    def authorize(self, actor, resource, row=None, write=False):
        if actor['status'] != 'ACTIVE':
            raise ForbiddenError()
        if actor['role'] == 'ADMIN' and resource not in ('assessments','answers'):
            return
        company = self.company(actor)
        if actor['role'] != 'ADMIN':
            if not company or self.require('companies', company)['status'] != 'ACTIVE':
                raise ForbiddenError()
        if write and resource not in ('assessments','answers'):
            raise ForbiddenError()
        if resource in ('assessments','answers'):
            assessment = row if resource == 'assessments' else self.require('assessments',row['avaliacao_id'], write)
            if actor['role'] != 'ADMIN' and assessment['empresa_id'] != company:
                raise ForbiddenError()
            if write and (actor['role'] != 'MANAGER' or assessment['gestor_usuario_id'] != actor['id']):
                raise ForbiddenError()
        elif resource == 'companies' and row['id'] != company:
            raise ForbiddenError()
        elif resource == 'users' and row['id'] != actor['id']:
            raise ForbiddenError()
        elif resource == 'memberships' and row['empresa_id'] != company:
            raise ForbiddenError()

    def read(self, actor, resource, identifier):
        row = self.require(resource, identifier)
        self.authorize(actor, resource, row)
        return self.public(row)

    def listing(self, actor, resource, offset=0, limit=50):
        result = []
        for row in self.repo.list(resource):
            try:
                self.authorize(actor,resource,row)
                result.append(self.public(row))
            except ForbiddenError:
                continue
        return {'items':result[offset:offset+limit], 'total':len(result)}

    @staticmethod
    def public(row):
        return {k:v for k,v in row.items() if k != 'senha_hash'}

    def version_for(self, resource, row):
        if resource == 'versions': return row
        if resource == 'dimensions': return self.require('versions',row['versao_questionario_id'],True)
        if resource == 'questions': return self.version_for('dimensions',self.require('dimensions',row['dimensao_id']))
        if resource == 'alternatives': return self.version_for('questions',self.require('questions',row['pergunta_id']))

    def writable(self, resource, row):
        version = self.version_for(resource,row)
        if version and version['status'] != 'DRAFT':
            raise ConflictError('Somente versões em rascunho podem ser modificadas.')
        if resource == 'questionnaires' and any(v['status'] != 'DRAFT' for v in self.repo.list('versions',{'questionario_id':row['id']})):
            raise ConflictError('Questionário possui versão publicada; preserve o histórico.')
        if resource in ('assessments','answers'):
            assessment = row if resource == 'assessments' else self.require('assessments',row['avaliacao_id'],True)
            if assessment['status'] != 'IN_PROGRESS':
                raise ConflictError('Avaliação não está em andamento.')

    def save(self, actor, resource, payload, identifier=None):
        if not isinstance(payload,dict) or set(payload) - EDITABLE[resource]:
            raise ValidationError('Campos desconhecidos ou JSON inválido.')
        old = self.require(resource,identifier,True) if identifier else None
        if old:
            self.authorize(actor,resource,old,True)
            self.writable(resource,old)
            if resource in ('assessments','answers','memberships'):
                for k in payload:
                    if k.endswith('_id') and payload[k] != old.get(k) and k != 'alternativa_id':
                        raise ValidationError('Não é permitido transferir este vínculo.')
        data = {**(old or {}), **payload}
        if resource == 'companies' and 'cnpj' in data:
            data['cnpj'] = normalize_cnpj(data['cnpj'])
        if resource == 'users':
            if 'senha' in data:
                password = data.pop('senha')
                if not isinstance(password,str) or len(password) < 7: raise ValidationError('Senha: mínimo de 7 caracteres.')
                data['senha_hash'] = self.hash_password(password)
            if 'email' in data and isinstance(data['email'],str): data['email'] = data['email'].strip().lower()
        if resource == 'assessments' and not old:
            data['gestor_usuario_id'] = actor['id']
        if resource == 'answers':
            assessment = self.require('assessments',data.get('avaliacao_id'),True)
            data['versao_questionario_id'] = assessment['versao_questionario_id']
            data['atualizado_por'] = actor['id']
            data['atualizado_em'] = datetime.now(timezone.utc).isoformat()
        try:
            entity = ENTITIES[resource](**data)
            data = asdict(entity)
        except (TypeError, ValueError) as exc:
            raise ValidationError('Campos obrigatórios ausentes ou tipos inválidos.') from exc
        data.pop('alternativas',None)
        for k,v in data.items():
            if hasattr(v,'value'): data[k] = v.value
            elif isinstance(v,datetime): data[k] = v.isoformat()
            elif not isinstance(v,(str,int,float,bool,type(None))): data[k] = str(v)
        self.authorize(actor,resource,data,True)
        self.writable(resource,data)
        self.validate(resource,data)
        return self.public(self.repo.save(resource,data))

    def validate(self, resource, data):
        for key,value in data.items():
            if key in ('ordem','pontuacao'):
                if type(value) is not int or value < 0: raise ValidationError(f'{key} deve ser inteiro não negativo.')
            elif value is not None and not isinstance(value,str):
                raise ValidationError(f'{key} deve ser texto.')
        for key in ('nome','razao_social','texto','codigo','email','cnpj','versao','versao_metodologia','senha_hash'):
            if key in data and not data[key].strip(): raise ValidationError(f'{key} não pode estar vazio.')
        if resource == 'users':
            if data['role'] not in ('ADMIN','MANAGER','IT_RESPONSIBLE'):
                raise ValidationError('role deve ser ADMIN, MANAGER ou IT_RESPONSIBLE.')
            if data['status'] not in ('ACTIVE','INACTIVE','PENDING'):
                raise ValidationError('status deve ser ACTIVE, INACTIVE ou PENDING.')
            if '@' not in data['email']: raise ValidationError('E-mail inválido.')
        if resource == 'companies':
            if data['status'] not in ('ACTIVE','INACTIVE'): raise ValidationError('Status inválido.')
            for company in self.repo.list('companies'):
                existing_cnpj = company.get('cnpj', '')
                if company['id'] != data['id'] and isinstance(existing_cnpj, str) and re.sub(r'[.\\/-]', '', existing_cnpj).upper() == data['cnpj']:
                    raise ConflictError('CNPJ já cadastrado.')
        if resource == 'memberships':
            self.require('companies',data['empresa_id'])
            user = self.require('users',data['usuario_id'])
            if user['role'] == 'ADMIN': raise ValidationError('Administrador não tem vínculo empresarial.')
        if resource == 'versions': self.require('questionnaires',data['questionario_id'])
        if resource == 'assessments':
            version = self.require('versions',data['versao_questionario_id'],True)
            if version['status'] != 'PUBLISHED': raise ValidationError('Selecione uma versão publicada.')
        if resource == 'answers':
            question = self.require('questions',data['pergunta_id'])
            if self.version_for('questions',question)['id'] != data['versao_questionario_id']:
                raise ValidationError('Pergunta de outra versão.')
            if data['tipo_resposta'] not in ('SCORED','NA','NS'): raise ValidationError('Tipo de resposta inválido.')
            if data['tipo_resposta'] == 'SCORED':
                if self.require('alternatives',data['alternativa_id'])['pergunta_id'] != data['pergunta_id']:
                    raise ValidationError('Alternativa de outra pergunta.')
            elif data['alternativa_id'] is not None: raise ValidationError('NA e NS não possuem alternativa.')
            if data['tipo_resposta'] == 'NA' and not (data['justificativa'] or '').strip(): raise ValidationError('Justificativa obrigatória.')

    def delete(self, actor, resource, identifier):
        row = self.require(resource,identifier,True)
        self.authorize(actor,resource,row,True)
        self.writable(resource,row)
        if resource in ('companies','users'):
            row['status'] = 'INACTIVE'
            self.repo.save(resource,row)
        elif resource == 'assessments':
            raise ConflictError('Avaliações são preservadas; exclusão não disponível.')
        else:
            self.repo.delete(resource,identifier)

    def result(self, actor, identifier):
        self.read(actor, 'assessments', identifier)
        rows = self.repo.list('assessment_results', {'avaliacao_id': identifier})
        if not rows:
            raise NotFoundError('resultado', identifier)
        return rows[0]['resultado']

    def finalize(self, actor, identifier):
        row = self.require('assessments', identifier, True)
        self.authorize(actor, 'assessments', row, True)
        if row['status'] == 'FINALIZED':
            return self.result(actor, identifier)
        self.writable('assessments', row)
        assessment = Assessment(**row)
        dimensions = [Dimension(**d) for d in self.repo.list('dimensions', {
            'versao_questionario_id': assessment.versao_questionario_id})]
        dimensions.sort(key=lambda d: d.ordem)
        questions = [Question(**q) for d in dimensions
                     for q in self.repo.list('questions', {'dimensao_id': d.id})]
        alternatives = {a['id']: Alternative(**a) for q in questions
                        for a in self.repo.list('alternatives', {'pergunta_id': q.id})}
        answers = [Answer(**a) for a in self.repo.list('answers', {'avaliacao_id': identifier})]
        calculated = MaturityCalculator().calculate(identifier, dimensions, questions, answers, alternatives)
        for dimension in calculated.dimensoes:
            dimension.avaliacao_resultado_id = calculated.id
        snapshot = json.loads(json.dumps(asdict(calculated), default=str))
        self.repo.save('assessment_results', {'id': str(calculated.id), 'avaliacao_id': identifier,
                                              'resultado': snapshot})
        assessment.finalize()
        row.update(status=assessment.status.value, finalizada_em=assessment.finalizada_em.isoformat())
        self.repo.save('assessments', row)
        return snapshot

    def publish(self, actor, identifier):
        row = self.require('versions',identifier,True)
        self.authorize(actor,'versions',row,True)
        self.writable('versions',row)
        dims = self.repo.list('dimensions',{'versao_questionario_id':identifier})
        counts = []
        for dim in dims:
            questions = self.repo.list('questions',{'dimensao_id':dim['id']})
            counts.append(len(questions))
            for question in questions:
                options = self.repo.list('alternatives',{'pergunta_id':question['id']})
                if sorted(a['pontuacao'] for a in options) != list(range(5)):
                    raise ValidationError('Cada pergunta exige cinco alternativas, de 0 a 4.')
        if sorted(counts) != [3,4,4,4,5,5,5]:
            raise ValidationError('O instrumento inicial exige sete dimensões e 30 perguntas (3,4,4,4,5,5,5).')
        row.update(status='PUBLISHED',publicado_em=datetime.now(timezone.utc).isoformat())
        return self.repo.save('versions',row)
