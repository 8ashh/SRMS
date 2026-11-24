from flask import session, has_request_context
from extensions import db
from models import AuditLog

class AuditService:
    @staticmethod
    def log(action, module, record_id=None, description=""):
        """
        Record a system or user action into the audit_logs table.
        Captures the session user_id if an authenticated request is active.
        """
        user_id = session.get('user_id') if has_request_context() else None
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=str(action),
                module=str(module),
                record_id=str(record_id) if record_id is not None else None,
                description=str(description)
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            # Do not crash the application if audit logging fails
            print(f"[AuditService Error] Failed to log action: {e}")
            return None

    @staticmethod
    def get_logs(limit=100, module=None, action=None):
        """Fetch latest audit logs for admin review."""
        query = AuditLog.query.order_by(AuditLog.timestamp.desc())
        if module:
            query = query.filter(AuditLog.module == module)
        if action:
            query = query.filter(AuditLog.action == action)
        return query.limit(limit).all()
