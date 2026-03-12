# models.py — backward-compatibility shim
# All models now live in auth_models.py and domain_models.py.
# This re-exports everything so existing imports keep working.
from .base          import Base
from .auth_models   import Role, User, UserRole, RefreshToken
from .domain_models import (
    InvoiceData, PaymentDetail, MatchingPaymentInvoice,
    EmailInbox, EmailAttachment,
    DisputeType, DisputeMaster,
    DisputeAIAnalysis, AnalysisSupportingRef,
    DisputeMemoryEpisode, DisputeMemorySummary,
    DisputeAssignment, DisputeOpenQuestion,
    DisputeActivityLog, DisputeStatusHistory,
)
