"""
Stripe service for OCR A-Level Computer Science AI Tutor
"""
from flask import current_app, g, url_for
from config.stripe_config import stripe_config
from models.subscription import Subscription
from models.user import User
from config.database_config import db
from datetime import datetime

class StripeService:
    """Stripe service class"""
    
    @staticmethod
    def get_stripe():
        """Get Stripe instance"""
        if 'stripe' not in g:
            g.stripe = stripe_config
        return g.stripe
    
    @staticmethod
    def get_plans():
        """Get subscription plans"""
        stripe_instance = StripeService.get_stripe()
        return stripe_instance.plans
    
    @staticmethod
    def create_checkout_session(user_id, plan_id):
        """Create a Stripe checkout session"""
        stripe_instance = StripeService.get_stripe()
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found: {user_id}")
            return None
        
        # Get plan
        plans = stripe_instance.plans
        if plan_id not in plans:
            current_app.logger.error(f"Plan not found: {plan_id}")
            return None
        
        plan = plans[plan_id]
        
        # Create success and cancel URLs
        success_url = url_for('subscription.checkout_success', plan_id=plan_id, _external=True)
        cancel_url = url_for('subscription.checkout_cancel', _external=True)
        
        # Create checkout session
        checkout_session = stripe_instance.create_checkout_session(
            plan['price_id'],
            user.email,
            success_url,
            cancel_url
        )
        
        if not checkout_session:
            return None
        
        return {
            'id': checkout_session.id,
            'url': checkout_session.url
        }
    
    @staticmethod
    def create_customer_portal_session(user_id):
        """Create a Stripe customer portal session"""
        stripe_instance = StripeService.get_stripe()
        
        # Get user's subscription
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription or not subscription.stripe_customer_id:
            current_app.logger.error(f"No subscription found for user: {user_id}")
            return None
        
        # Create return URL
        return_url = url_for('subscription.manage', _external=True)
        
        # Create customer portal session
        portal_session = stripe_instance.create_customer_portal_session(
            subscription.stripe_customer_id,
            return_url
        )
        
        if not portal_session:
            return None
        
        return {
            'id': portal_session.id,
            'url': portal_session.url
        }
    
    @staticmethod
    def handle_checkout_success(session_id, user_id, plan_id):
        """Handle checkout success"""
        import stripe
        
        try:
            # Retrieve checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Get subscription ID and customer ID
            subscription_id = session.subscription
            customer_id = session.customer
            
            # Retrieve subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get plan
            stripe_instance = StripeService.get_stripe()
            plans = stripe_instance.plans
            if plan_id not in plans:
                current_app.logger.error(f"Plan not found: {plan_id}")
                return False
            
            # Create or update subscription
            subscription = Subscription.query.filter_by(user_id=user_id).first()
            
            if subscription:
                # Update existing subscription
                subscription.stripe_subscription_id = subscription_id
                subscription.stripe_customer_id = customer_id
                subscription.plan = plan_id
                subscription.status = stripe_subscription.status
                subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
            else:
                # Create new subscription
                subscription = Subscription(
                    user_id=user_id,
                    plan=plan_id,
                    status=stripe_subscription.status,
                    current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                    current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    cancel_at_period_end=stripe_subscription.cancel_at_period_end
                )
                db.session.add(subscription)
            
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error handling checkout success: {e}")
            return False
    
    @staticmethod
    def cancel_subscription(user_id, at_period_end=True):
        """Cancel a subscription"""
        import stripe
        
        # Get user's subscription
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription or not subscription.stripe_subscription_id:
            current_app.logger.error(f"No subscription found for user: {user_id}")
            return False
        
        try:
            # Cancel subscription in Stripe
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=at_period_end
            )
            
            # Update subscription in database
            if at_period_end:
                subscription.cancel_at_period_end = True
            else:
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error canceling subscription: {e}")
            return False
    
    @staticmethod
    def handle_webhook_event(payload, sig_header):
        """Handle Stripe webhook event"""
        stripe_instance = StripeService.get_stripe()
        
        # Verify webhook signature
        event = stripe_instance.construct_event(payload, sig_header)
        if not event:
            return False
        
        # Handle different event types
        if event.type == 'checkout.session.completed':
            # Handle checkout session completed
            session = event.data.object
            
            # Get client reference ID (user_id:plan_id)
            client_reference_id = session.get('client_reference_id')
            if not client_reference_id or ':' not in client_reference_id:
                current_app.logger.error(f"Invalid client reference ID: {client_reference_id}")
                return False
            
            user_id, plan_id = client_reference_id.split(':', 1)
            
            # Handle checkout success
            return StripeService.handle_checkout_success(session.id, int(user_id), plan_id)
            
        elif event.type == 'customer.subscription.updated':
            # Handle subscription updated
            stripe_subscription = event.data.object
            
            # Find subscription in database
            subscription = Subscription.query.filter_by(stripe_subscription_id=stripe_subscription.id).first()
            if not subscription:
                current_app.logger.error(f"Subscription not found: {stripe_subscription.id}")
                return False
            
            # Update subscription
            subscription.update_from_stripe(stripe_subscription)
            return True
            
        elif event.type == 'customer.subscription.deleted':
            # Handle subscription deleted
            stripe_subscription = event.data.object
            
            # Find subscription in database
            subscription = Subscription.query.filter_by(stripe_subscription_id=stripe_subscription.id).first()
            if not subscription:
                current_app.logger.error(f"Subscription not found: {stripe_subscription.id}")
                return False
            
            # Update subscription
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
            db.session.commit()
            return True
        
        # Other event types
        return True
