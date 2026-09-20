// key: P4
// description: Manager may approve partial plan with upfront >= 25% and installments <= 6
permit(
  principal == Relief::Manager::"manager-tier",
  action == Relief::Action::"OfferPartialPlan",
  resource is Relief::Loan
)
when {
  context.upfrontPct >= 25 &&
  context.installments <= 6 &&
  resource.dpd <= 60 &&
  resource.priorReliefs < 3 &&
  !resource.legalHold
};
