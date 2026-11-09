from sqlalchemy import select, insert, update, delete
from prismati.infrastructure.persistence.models.tables import TABLES

class SqlCatalog:
    def __init__(self, session):
        self.session = session

    def get(self, resource, identifier, lock=False):
        t = TABLES[resource]
        query = select(t).where(t.c.id == identifier)
        if lock:
            query = query.with_for_update()
        row = self.session.execute(query).mappings().first()
        return dict(row) if row else None

    def list(self, resource, filters=None):
        t = TABLES[resource]
        query = select(t).order_by(t.c.id)
        for name, value in (filters or {}).items():
            query = query.where(t.c[name] == value)
        return [dict(r) for r in self.session.execute(query).mappings()]

    def save(self, resource, data):
        t = TABLES[resource]
        if self.get(resource, data['id']):
            self.session.execute(update(t).where(t.c.id == data['id']).values(**data))
        else:
            self.session.execute(insert(t).values(**data))
        self.audit(resource, data['id'], 'salvar')
        return data

    def audit(self, resource, identifier, action):
        from flask import has_request_context, g
        from datetime import datetime, timezone
        from uuid import uuid4
        if resource not in ('audit', 'login_limits'):
            actor = getattr(g, 'actor_id', 'sistema') if has_request_context() else 'sistema'
            self.session.execute(insert(TABLES['audit']).values(id=str(uuid4()), ator=actor,
                acao=action, recurso=resource, registro=identifier, data=datetime.now(timezone.utc).isoformat()))

    def delete(self, resource, identifier):
        t = TABLES[resource]
        self.session.execute(delete(t).where(t.c.id == identifier))
        self.audit(resource, identifier, 'excluir')
