"""Initial schema creation - All models from Phases 1-9

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='analyst'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uc_users_email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.String(100), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('kyc_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('kyc_verification_date', sa.DateTime(), nullable=True),
        sa.Column('account_status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('risk_profile', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uc_customers_customer_id')
    )
    op.create_index('ix_customers_customer_id', 'customers', ['customer_id'])
    op.create_index('ix_customers_email', 'customers', ['email'])
    op.create_index('ix_customers_risk_profile', 'customers', ['risk_profile'])

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(100), nullable=False, unique=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.String(100), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='completed'),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('mcc_code', sa.String(10), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id', name='uc_transactions_transaction_id')
    )
    op.create_index('ix_transactions_transaction_id', 'transactions', ['transaction_id'])
    op.create_index('ix_transactions_customer_id', 'transactions', ['customer_id'])
    op.create_index('ix_transactions_transaction_date', 'transactions', ['transaction_date'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_amount', 'transactions', ['amount'])

    # Create fraud_rules table
    op.create_table(
        'fraud_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_logic', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_rules_rule_name', 'fraud_rules', ['rule_name'])
    op.create_index('ix_fraud_rules_is_active', 'fraud_rules', ['is_active'])
    op.create_index('ix_fraud_rules_severity', 'fraud_rules', ['severity'])

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.String(100), nullable=False, unique=True),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('fraud_rule_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fraud_rule_id'], ['fraud_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_id', name='uc_alerts_alert_id')
    )
    op.create_index('ix_alerts_alert_id', 'alerts', ['alert_id'])
    op.create_index('ix_alerts_transaction_id', 'alerts', ['transaction_id'])
    op.create_index('ix_alerts_customer_id', 'alerts', ['customer_id'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_risk_score', 'alerts', ['risk_score'])

    # Create investigation_cases table
    op.create_table(
        'investigation_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.String(100), nullable=False, unique=True),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('case_status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('case_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id', name='uc_investigation_cases_case_id')
    )
    op.create_index('ix_investigation_cases_case_id', 'investigation_cases', ['case_id'])
    op.create_index('ix_investigation_cases_alert_id', 'investigation_cases', ['alert_id'])
    op.create_index('ix_investigation_cases_customer_id', 'investigation_cases', ['customer_id'])
    op.create_index('ix_investigation_cases_case_status', 'investigation_cases', ['case_status'])
    op.create_index('ix_investigation_cases_priority', 'investigation_cases', ['priority'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('target_id_str', sa.String(100), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_target_type', 'audit_logs', ['target_type'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # Create risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('assessment_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_risk_assessments_customer_id', 'risk_assessments', ['customer_id'])
    op.create_index('ix_risk_assessments_transaction_id', 'risk_assessments', ['transaction_id'])
    op.create_index('ix_risk_assessments_risk_score', 'risk_assessments', ['risk_score'])
    op.create_index('ix_risk_assessments_assessment_date', 'risk_assessments', ['assessment_date'])

    # Create ml_model_logs table
    op.create_table(
        'ml_model_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('prediction', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('input_features', sa.JSON(), nullable=True),
        sa.Column('actual_label', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ml_model_logs_model_name', 'ml_model_logs', ['model_name'])
    op.create_index('ix_ml_model_logs_created_at', 'ml_model_logs', ['created_at'])


def downgrade():
    op.drop_index('ix_ml_model_logs_created_at', 'ml_model_logs')
    op.drop_index('ix_ml_model_logs_model_name', 'ml_model_logs')
    op.drop_table('ml_model_logs')
    
    op.drop_index('ix_risk_assessments_assessment_date', 'risk_assessments')
    op.drop_index('ix_risk_assessments_risk_score', 'risk_assessments')
    op.drop_index('ix_risk_assessments_transaction_id', 'risk_assessments')
    op.drop_index('ix_risk_assessments_customer_id', 'risk_assessments')
    op.drop_table('risk_assessments')
    
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_audit_logs_target_type', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_actor_id', 'audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_investigation_cases_priority', 'investigation_cases')
    op.drop_index('ix_investigation_cases_case_status', 'investigation_cases')
    op.drop_index('ix_investigation_cases_customer_id', 'investigation_cases')
    op.drop_index('ix_investigation_cases_alert_id', 'investigation_cases')
    op.drop_index('ix_investigation_cases_case_id', 'investigation_cases')
    op.drop_table('investigation_cases')
    
    op.drop_index('ix_alerts_risk_score', 'alerts')
    op.drop_index('ix_alerts_severity', 'alerts')
    op.drop_index('ix_alerts_status', 'alerts')
    op.drop_index('ix_alerts_customer_id', 'alerts')
    op.drop_index('ix_alerts_transaction_id', 'alerts')
    op.drop_index('ix_alerts_alert_id', 'alerts')
    op.drop_table('alerts')
    
    op.drop_index('ix_fraud_rules_severity', 'fraud_rules')
    op.drop_index('ix_fraud_rules_is_active', 'fraud_rules')
    op.drop_index('ix_fraud_rules_rule_name', 'fraud_rules')
    op.drop_table('fraud_rules')
    
    op.drop_index('ix_transactions_amount', 'transactions')
    op.drop_index('ix_transactions_status', 'transactions')
    op.drop_index('ix_transactions_transaction_date', 'transactions')
    op.drop_index('ix_transactions_customer_id', 'transactions')
    op.drop_index('ix_transactions_transaction_id', 'transactions')
    op.drop_table('transactions')
    
    op.drop_index('ix_customers_risk_profile', 'customers')
    op.drop_index('ix_customers_email', 'customers')
    op.drop_index('ix_customers_customer_id', 'customers')
    op.drop_table('customers')
    
    op.drop_index('ix_users_role', 'users')
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
