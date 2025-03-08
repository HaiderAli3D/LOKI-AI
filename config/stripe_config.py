"""
Stripe configuration for OCR A-Level Computer Science AI Tutor
"""
import os
import stripe

class StripeConfig:
    """Stripe configuration class"""
    
    def __init__(self, app=None):
        """Initialize Stripe configuration"""
        self.app = app
        
        # Stripe API keys
        self.publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
        self.secret_key = os.environ.get('STRIPE_SECRET_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        # Subscription plans
        self.plans = self._load_plans()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Stripe with Flask app"""
        self.app = app
        
        # Configure Stripe
        stripe.api_key = self.secret_key
        
        # Add Stripe to Flask app context
        app.extensions['stripe'] = self
        
        # Add Stripe publishable key to templates
        @app.context_processor
        def inject_stripe_key():
            return {'stripe_key': self.publishable_key}
        
        return self
    
    def _load_plans(self):
        """Load subscription plans from environment variables"""
        plans = {}
        
        # Basic plan
        basic_plan = os.environ.get('STRIPE_BASIC_PLAN', '')
        if basic_plan and ':' in basic_plan:
            plan_id, price_id = basic_plan.split(':', 1)
            plans['basic'] = {
                'id': plan_id,
                'price_id': price_id,
                'name': 'Basic',
                'price': 9.99,
                'interval': 'month',
                'features': [
                    'Access to all topics',
                    'Basic learning modes',
                    'Progress tracking'
                ],
                'recommended': False
            }
        
        # Premium plan
        premium_plan = os.environ.get('STRIPE_PREMIUM_PLAN', '')
        if premium_plan and ':' in premium_plan:
            plan_id, price_id = premium_plan.split(':', 1)
            plans['premium'] = {
                'id': plan_id,
                'price_id': price_id,
                'name': 'Premium',
                'price': 19.99,
                'interval': 'month',
                'features': [
                    'Access to all topics',
                    'All learning modes',
                    'Advanced progress tracking',
                    'Advanced practice questions',
                    'Exam simulation'
                ],
                'recommended': True
            }
        
        # Enterprise plan
        enterprise_plan = os.environ.get('STRIPE_ENTERPRISE_PLAN', '')
        if enterprise_plan and ':' in enterprise_plan:
            plan_id, price_id = enterprise_plan.split(':', 1)
            plans['enterprise'] = {
                'id': plan_id,
                'price_id': price_id,
                'name': 'Enterprise',
                'price': 99.99,
                'interval': 'month',
                'features': [
                    'Access to all topics',
                    'All learning modes',
                    'Advanced progress tracking',
                    'Advanced practice questions',
                    'Exam simulation',
                    'Priority support',
                    'Custom learning paths',
                    'Team management'
                ],
                'recommended': False
            }
        
        return plans
    
    def create_checkout_session(self, price_id, customer_email, success_url, cancel_url):
        """Create a Stripe checkout session"""
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=customer_email,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url
            )
            return checkout_session
        except Exception as e:
            self.app.logger.error(f"Error creating Stripe checkout session: {e}")
            return None
    
    def create_customer_portal_session(self, customer_id, return_url):
        """Create a Stripe customer portal session"""
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return portal_session
        except Exception as e:
            self.app.logger.error(f"Error creating Stripe customer portal session: {e}")
            return None
    
    def get_subscription(self, subscription_id):
        """Get a Stripe subscription"""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except Exception as e:
            self.app.logger.error(f"Error retrieving Stripe subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id, at_period_end=True):
        """Cancel a Stripe subscription"""
        try:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=at_period_end
            )
        except Exception as e:
            self.app.logger.error(f"Error canceling Stripe subscription: {e}")
            return None
    
    def get_customer(self, customer_id):
        """Get a Stripe customer"""
        try:
            return stripe.Customer.retrieve(customer_id)
        except Exception as e:
            self.app.logger.error(f"Error retrieving Stripe customer: {e}")
            return None
    
    def get_payment_method(self, payment_method_id):
        """Get a Stripe payment method"""
        try:
            return stripe.PaymentMethod.retrieve(payment_method_id)
        except Exception as e:
            self.app.logger.error(f"Error retrieving Stripe payment method: {e}")
            return None
    
    def get_invoices(self, customer_id, limit=10):
        """Get Stripe invoices for a customer"""
        try:
            return stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
        except Exception as e:
            self.app.logger.error(f"Error retrieving Stripe invoices: {e}")
            return None
    
    def construct_event(self, payload, sig_header):
        """Construct a Stripe event from webhook payload"""
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except Exception as e:
            self.app.logger.error(f"Error constructing Stripe event: {e}")
            return None

# Create Stripe configuration instance
stripe_config = StripeConfig()
