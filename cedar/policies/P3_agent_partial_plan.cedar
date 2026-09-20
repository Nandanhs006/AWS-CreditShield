// key: P3
// description: Agent may offer partial plan with upfront >= 50% and installments <= 3
permit(
  principal == Relief::AiAgent::"agent-v1",
  action == Relief::Action::"OfferPartialPlan",
  resource is Relief::Loan
)
when {
  context.upfrontPct >= 50 &&
  context.installments <= 3 &&
  resource.dpd <= 30 &&
  resource.priorReliefs < 2 &&
  !resource.legalHold
};
