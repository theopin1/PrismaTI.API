"""Modelo relacional inicial; todas as exclusões referenciadas são restritas."""
from sqlalchemy import (MetaData, Table, Column, String, Integer, ForeignKey,
                        UniqueConstraint, CheckConstraint, Index, text)

metadata = MetaData()

def table(name, *columns, constraints=()):
    return Table(name, metadata, Column('id', String(36), primary_key=True), *columns, *constraints)

def s(name, nullable=False):
    return Column(name, String, nullable=nullable)

def fk(name, target, nullable=False):
    return Column(name, String(36), ForeignKey(target + '.id', ondelete='RESTRICT'), nullable=nullable)

companies = table('companies', s('razao_social'), s('cnpj'), s('segmento'), s('porte'), s('status'), s('criado_em'), constraints=(UniqueConstraint('cnpj'),))
users = table('users', s('nome'), s('email'), s('senha_hash'), s('role'), s('status'), s('data_criacao'), constraints=(UniqueConstraint('email'),))
memberships = table('memberships', fk('empresa_id','companies'), fk('usuario_id','users'), s('criado_em'), constraints=(UniqueConstraint('usuario_id'),))
questionnaires = table('questionnaires', s('nome'), s('descricao'), s('status'))
versions = table('versions', fk('questionario_id','questionnaires'), s('versao'), s('versao_metodologia'), s('status'), s('publicado_em',True), constraints=(UniqueConstraint('questionario_id','versao'),))
dimensions = table('dimensions', fk('versao_questionario_id','versions'), s('nome'), s('descricao'), Column('ordem',Integer,nullable=False), s('codigo'), constraints=(UniqueConstraint('versao_questionario_id','codigo'),))
questions = table('questions', fk('dimensao_id','dimensions'), s('texto'), Column('ordem',Integer,nullable=False), s('codigo'), s('explicacao'), s('orientacao_evidencia'), constraints=(UniqueConstraint('dimensao_id','codigo'),))
alternatives = table('alternatives', fk('pergunta_id','questions'), s('descricao'), Column('pontuacao',Integer,nullable=False), Column('ordem',Integer,nullable=False), constraints=(CheckConstraint('pontuacao BETWEEN 0 AND 4'),UniqueConstraint('pergunta_id','pontuacao')))
assessments = table('assessments', fk('empresa_id','companies'), fk('gestor_usuario_id','users'), fk('versao_questionario_id','versions'), s('status'), s('iniciada_em'), s('finalizada_em',True))
Index('one_open_assessment_per_company',assessments.c.empresa_id,unique=True,postgresql_where=text("status = 'IN_PROGRESS'"))
answers = table('answers', fk('avaliacao_id','assessments'), fk('pergunta_id','questions'), fk('versao_questionario_id','versions'), s('tipo_resposta'), fk('alternativa_id','alternatives',True), s('justificativa',True), fk('atualizado_por','users'), s('atualizado_em'), constraints=(UniqueConstraint('avaliacao_id','pergunta_id'),CheckConstraint("(tipo_resposta = 'SCORED' AND alternativa_id IS NOT NULL) OR (tipo_resposta IN ('NA','NS') AND alternativa_id IS NULL)"),CheckConstraint("tipo_resposta <> 'NA' OR (justificativa IS NOT NULL AND length(trim(justificativa)) > 0)")))
from sqlalchemy import JSON

assessment_results = table('assessment_results', fk('avaliacao_id', 'assessments'),
                           Column('resultado', JSON, nullable=False),
                           constraints=(UniqueConstraint('avaliacao_id'),))
from sqlalchemy import LargeBinary

access_links = table('access_links', s('digest'), s('tipo'), s('expira'), s('email'), s('usuario_id', True), s('empresa_id', True), s('perfil', True), s('usado', True), constraints=(UniqueConstraint('digest'),))
evidence = table('evidence', fk('resposta_id','answers'), fk('autor','users'), s('nome'), s('url', True), Column('arquivo', LargeBinary))
reports = table('reports', fk('avaliacao_id','assessments'), s('status'), s('criado_em'), s('texto', True), s('modelo', True), Column('uso', JSON))
audit = table('audit', s('ator'), s('acao'), s('recurso'), s('registro'), s('data'))
login_limits = table('login_limits', Column('inicio', Integer, nullable=False), Column('tentativas', Integer, nullable=False))
TABLES = {t.name: t for t in metadata.tables.values()}
