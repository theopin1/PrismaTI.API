import copy
import unittest
from prismati.application.use_cases.catalog import CatalogService, ENTITIES
from prismati.domain.exceptions.domain_exceptions import ForbiddenError, ValidationError, ConflictError

class MemoryCatalog:
    def __init__(self): self.data = {k:{} for k in ENTITIES}
    def get(self,r,i,lock=False): return copy.deepcopy(self.data[r].get(i))
    def list(self,r,filters=None): return [copy.deepcopy(v) for v in self.data[r].values() if all(v.get(k)==x for k,x in (filters or {}).items())]
    def save(self,r,d): self.data[r][d['id']]=copy.deepcopy(d); return d
    def delete(self,r,i): del self.data[r][i]

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.repo=MemoryCatalog()
        self.service=CatalogService(self.repo,lambda p:'hashed:'+p)
        self.admin={'id':'admin','status':'ACTIVE','role':'ADMIN'}

    def test_password_never_returned(self):
        user=self.service.save(self.admin,'users',dict(nome='Gestor',email='G@EXAMPLE.COM',senha='long-password-123',role='MANAGER',status='ACTIVE'))
        self.assertNotIn('senha_hash',user)
        self.assertEqual(user['email'],'g@example.com')
        self.assertTrue(self.repo.get('users',user['id'])['senha_hash'].startswith('hashed:'))

    def test_company_deletion_preserves_record(self):
        company=self.service.save(self.admin,'companies',dict(razao_social='Empresa',cnpj='12345678000190',segmento='TI',porte='PME'))
        self.service.delete(self.admin,'companies',company['id'])
        self.assertEqual(self.repo.get('companies',company['id'])['status'],'INACTIVE')

    def test_password_minimum_on_creation_and_update(self):
        payload = dict(nome='Gestor', email='gestor@example.com', senha='123456', role='MANAGER', status='ACTIVE')
        with self.assertRaisesRegex(ValidationError, 'mínimo de 7'):
            self.service.save(self.admin, 'users', payload)
        payload['senha'] = '1234567'
        user = self.service.save(self.admin, 'users', payload)
        with self.assertRaisesRegex(ValidationError, 'mínimo de 7'):
            self.service.save(self.admin, 'users', {'senha': '123456'}, user['id'])
        self.service.save(self.admin, 'users', {'senha': '7654321'}, user['id'])
        self.assertEqual(self.repo.get('users', user['id'])['senha_hash'], 'hashed:7654321')

    def test_forbids_read_other_company(self):
        self.repo.save('companies',dict(id='a',status='ACTIVE'))
        self.repo.save('companies',dict(id='b',status='ACTIVE'))
        self.repo.save('memberships',dict(id='link',empresa_id='a',usuario_id='u'))
        with self.assertRaises(ForbiddenError):
            self.service.read(dict(id='u',status='ACTIVE',role='MANAGER'),'companies','b')

    def test_published_dimension_is_immutable(self):
        self.repo.save('versions',dict(id='v',status='PUBLISHED'))
        self.repo.save('dimensions',dict(id='d',versao_questionario_id='v'))
        with self.assertRaises(ConflictError):
            self.service.save(self.admin,'dimensions',{'nome':'changed'},'d')

    def test_empty_instrument_cannot_be_published(self):
        self.repo.save('versions',dict(id='v',status='DRAFT'))
        with self.assertRaises(ValidationError): self.service.publish(self.admin,'v')

    def test_rejects_mass_assignment(self):
        with self.assertRaises(ValidationError): self.service.save(self.admin,'users',{'senha_hash':'unsafe'})

    def test_cnpj_format_on_creation_and_update(self):
        payload = dict(razao_social='Empresa', cnpj='12.345.678/0001-90', segmento='TI', porte='PME')
        company = self.service.save(self.admin, 'companies', payload)
        self.assertEqual(company['cnpj'], '12345678000190')
        for invalid in ('123', '1234567800019', '123456780001900', '1234567800019A',
                        'AB.CDE.FGH/IJKL-MN', '１２３４５６７８０００１９０', '', None,
                        12345678000190, '12.345.678/0001-90 ', '12.ABÇ.345/01DE-35',
                        '12345678000190\n'):
            with self.subTest(cnpj=invalid):
                with self.assertRaises(ValidationError):
                    self.service.save(self.admin, 'companies', {**payload, 'cnpj': invalid})
                with self.assertRaises(ValidationError):
                    self.service.save(self.admin, 'companies', {'cnpj': invalid}, company['id'])
        updated = self.service.save(self.admin, 'companies', {'cnpj': '00000000000191'}, company['id'])
        self.assertEqual(updated['cnpj'], '00000000000191')
        self.assertEqual(self.repo.get('companies', company['id'])['cnpj'], '00000000000191')

    def test_cnpj_duplicate_ignores_mask_and_allows_own_update(self):
        payload = dict(razao_social='Empresa', cnpj='12345678000190', segmento='TI', porte='PME')
        company = self.service.save(self.admin, 'companies', payload)
        with self.assertRaises(ConflictError):
            self.service.save(self.admin, 'companies', {**payload, 'cnpj': '12.345.678/0001-90'})
        self.service.save(self.admin, 'companies', {'cnpj': '12.345.678/0001-90'}, company['id'])
        self.repo.data['companies'][company['id']]['cnpj'] = '12.345.678/0001-90'
        with self.assertRaises(ConflictError):
            self.service.save(self.admin, 'companies', payload)

    def test_alphanumeric_cnpj_normalization_and_duplicates(self):
        payload = dict(razao_social='Empresa', cnpj='12.abc.345/01de-35', segmento='TI', porte='PME')
        company = self.service.save(self.admin, 'companies', payload)
        self.assertEqual(company['cnpj'], '12ABC34501DE35')
        for value in ('12ABC34501DE35', r'12.abc.345\01de-35', '12-abc/345.01de35'):
            with self.subTest(cnpj=value):
                updated = self.service.save(self.admin, 'companies', {'cnpj': value}, company['id'])
                self.assertEqual(updated['cnpj'], '12ABC34501DE35')
                with self.assertRaises(ConflictError):
                    self.service.save(self.admin, 'companies', {**payload, 'cnpj': value})
        self.repo.data['companies'][company['id']]['cnpj'] = r'12.abc.345\01de-35'
        with self.assertRaises(ConflictError):
            self.service.save(self.admin, 'companies', {**payload, 'cnpj': '12ABC34501DE35'})
