class CEOBrainService:
    def build_summary(self, metrics: dict) -> dict:
        health = "healthy" if metrics.get("payments_pending", 0) < 5 else "warning"
        return {
            "executive_summary": "הפלטפורמה במצב הפעלה תפעולי. שמור על זרימת לידים, צור תצוגות מקדימות חזקות לדראפטים ופנה תקיעות תשלום במהירות.",
            "health": health,
            "recommended_actions": [
                "סקור לידים בעלי ציון גבוה ראשון",
                "צור תצוגות מקדימות חסרות לדראפטים עבור עסקים מוכנים לפנייה",
                "פנה אישורי תשלום ממתינים",
            ],
            "metrics": metrics,
        }
