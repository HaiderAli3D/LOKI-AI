"""
Subscription routes for OCR A-Level Computer Science AI Tutor
"""
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from routes import subscription_bp
from models.subscription import Subscription
from services.stripe_service import StripeService
from config.database_config import db
from datetime import datetime

@subscription_bp.route('/plans')
def plans():
    """Subscription plans page"""
    # Get plans from Stripe
    plans = StripeService.get_plans()
    
    # Check if user has subscription
    has_subscription = False
    if current_user.is_authenticated:
        has_subscription = current_user.has_active_subscription()
    
    return render_template('subscription/plans.html', plans=plans, has_subscription=has_subscription)

@subscription_bp.route('/checkout/<plan_id>')
@login_required
def checkout(plan_id):
    """Checkout page for a subscription plan"""
    # Check if user already has subscription
    if current_user.has_active_subscription():
        flash('You already have an active subscription', 'info')
        return redirect(url_for('subscription.manage'))
    
    # Create checkout session
    checkout_session = StripeService.create_checkout_session(current_user.id, plan_id)
    
    if not checkout_session:
        flash('Error creating checkout session', 'danger')
        return redirect(url_for('subscription.plans'))
    
    # Redirect to Stripe checkout
    return redirect(checkout_session['url'])

@subscription_bp.route('/checkout/success')
@login_required
def checkout_success():
    """Checkout success page"""
    # Get session ID and plan ID from query parameters
    session_id = request.args.get('session_id')
    plan_id = request.args.get('plan_id')
    
    if not session_id or not plan_id:
        flash('Invalid checkout session', 'danger')
        return redirect(url_for('subscription.plans'))
    
    # Handle checkout success
    success = StripeService.handle_checkout_success(session_id, current_user.id, plan_id)
    
    if not success:
        flash('Error processing subscription', 'danger')
        return redirect(url_for('subscription.plans'))
    
    flash('Subscription activated successfully', 'success')
    return redirect(url_for('subscription.manage'))

@subscription_bp.route('/checkout/cancel')
@login_required
def checkout_cancel():
    """Checkout cancel page"""
    flash('Checkout canceled', 'info')
    return redirect(url_for('subscription.plans'))

@subscription_bp.route('/manage')
@login_required
def manage():
    """Subscription management page"""
    # Get user's subscription
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    # Check if user has subscription
    has_subscription = subscription is not None and subscription.is_active()
    
    # Get customer portal URL if user has subscription
    customer_portal_url = None
    if has_subscription and subscription.stripe_customer_id:
        portal_session = StripeService.create_customer_portal_session(current_user.id)
        if portal_session:
            customer_portal_url = portal_session['url']
    
    # Get invoices if user has subscription
    invoices = []
    if has_subscription and subscription.stripe_customer_id:
        import stripe
        try:
            invoice_list = stripe.Invoice.list(
                customer=subscription.stripe_customer_id,
                limit=10
            )
            
            for invoice in invoice_list.data:
                invoices.append({
                    'date': datetime.fromtimestamp(invoice.created),
                    'description': invoice.lines.data[0].description if invoice.lines.data else 'Subscription',
                    'amount': invoice.amount_paid / 100.0
                })
        except Exception as e:
            current_app.logger.error(f"Error getting invoices: {e}")
    
    return render_template('subscription/manage.html', 
                          subscription=subscription, 
                          has_subscription=has_subscription,
                          customer_portal_url=customer_portal_url,
                          invoices=invoices)

@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription"""
    # Get at_period_end parameter
    at_period_end = request.form.get('at_period_end', 'true') == 'true'
    
    # Cancel subscription
    success = StripeService.cancel_subscription(current_user.id, at_period_end)
    
    if not success:
        flash('Error canceling subscription', 'danger')
        return redirect(url_for('subscription.manage'))
    
    if at_period_end:
        flash('Your subscription will be canceled at the end of the current billing period', 'info')
    else:
        flash('Your subscription has been canceled', 'info')
    
    return redirect(url_for('subscription.manage'))

@subscription_bp.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook endpoint"""
    # Get Stripe signature
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return jsonify({'error': 'No Stripe signature'}), 400
    
    # Get request payload
    payload = request.data
    
    # Handle webhook event
    success = StripeService.handle_webhook_event(payload, sig_header)
    
    if not success:
        return jsonify({'error': 'Error handling webhook event'}), 400
    
    return jsonify({'success': True})

@subscription_bp.route('/check')
@login_required
def check_subscription():
    """Check subscription status"""
    # Check if user has subscription
    has_subscription = current_user.has_active_subscription()
    
    return jsonify({
        'has_subscription': has_subscription,
        'subscription': current_user.subscription.to_dict() if has_subscription else None
    })
