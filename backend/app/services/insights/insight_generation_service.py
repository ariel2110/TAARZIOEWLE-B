from sqlalchemy.orm import Session
from app.models.generated_insight import GeneratedInsight


class InsightGenerationService:
    def list_insights(self, db: Session):
        return db.query(GeneratedInsight).order_by(GeneratedInsight.created_at.desc()).all()

    def seed_default_insight(self, db: Session):
        item = db.query(GeneratedInsight).first()
        if item:
            return item
        item = GeneratedInsight(
            insight_type='operations',
            title='Follow-up queue should be monitored daily',
            summary='When follow-ups are delayed, conversion quality usually drops. Keep a daily review queue.',
            confidence_score=0.72,
            status='proposed',
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
