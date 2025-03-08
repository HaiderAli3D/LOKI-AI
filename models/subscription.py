"""
Subscription model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
from config.database_config import db

class Subscription(db.Model):
    """Subscription model"""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(128), nullable=True)
    stripe_subscription_id = db.Column(db.String(128), nullable=True)
    plan = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    canceled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id, plan, status, current_period_start, current_period_end, 
                 stripe_customer_id=None, stripe_subscription_id=None, cancel_at_period_end=False):
        """Initialize subscription"""
        self.user_id = user_id
        self.plan = plan
        self.status = status
        self.current_period_start = current_period_start
        self.current_period_end = current_period_end
        self.stripe_customer_id = stripe_customer_id
        self.stripe_subscription_id = stripe_subscription_id
        self.cancel_at_period_end = cancel_at_period_end
    
    def is_active(self):
        """Check if subscription is active"""
        return self.status in ['active', 'trialing'] and datetime.utcnow() <= self.current_period_end
    
    def is_canceled(self):
        """Check if subscription is canceled"""
        return self.status == 'canceled' or self.cancel_at_period_end
    
    def cancel(self, at_period_end=True):
        """Cancel subscription"""
        if at_period_end:
            self.cancel_at_period_end = True
        else:
            self.status = 'canceled'
            self.canceled_at = datetime.utcnow()
        db.session.commit()
    
    def reactivate(self):
        """Reactivate subscription"""
        if self.cancel_at_period_end:
            self.cancel_at_period_end = False
            db.session.commit()
            return True
        return False
    
    def update_from_stripe(self, stripe_subscription):
        """Update subscription from Stripe subscription object"""
        self.status = stripe_subscription.status
        self.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        self.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        self.cancel_at_period_end = stripe_subscription.cancel_at_period_end
        
        if hasattr(stripe_subscription, 'canceled_at') and stripe_subscription.canceled_at:
            self.canceled_at = datetime.fromtimestamp(stripe_subscription.canceled_at)
        
        db.session.commit()
    
    def get_plan_details(self):
        """Get plan details"""
        from config.stripe_config import stripe_config
        
        plans = stripe_config.plans
        if self.plan in plans:
            return plans[self.plan]
        
        # Default plan details if not found
        return {
            'name': self.plan.capitalize(),
            'price': 0,
            'interval': 'month',
            'features': []
        }
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        plan_details = self.get_plan_details()
        
        return {
            'id': self.id,
            'plan': self.plan,
            'plan_name': plan_details['name'],
            'price': plan_details['price'],
            'interval': plan_details['interval'],
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'is_active': self.is_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """String representation of subscription"""
        return f'<Subscription {self.id} {self.plan} {self.status}>'
