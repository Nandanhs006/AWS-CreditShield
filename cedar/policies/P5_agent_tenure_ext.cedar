// key: P5
// description: Agent may extend tenure up to 3 months when dpd <= 30 and no earlier reliefs
permit(
  principal == Relief::AiAgent::"agent-v1",
  action == Relief::Action::"OfferTenureExtension",
  resource is Relief::Loan
)
when {
  context.months > 0 && context.months <= 3 &&
  resource.dpd <= 30 &&
  resource.priorReliefs == 0 &&
  !resource.legalHold
};
