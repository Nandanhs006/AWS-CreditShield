// key: P7
// description: Agent may waive late fees up to 500 when dpd <= 30 and prior reliefs < 2
permit(
  principal == Relief::AiAgent::"agent-v1",
  action == Relief::Action::"OfferFeeWaiver",
  resource is Relief::Loan
)
when {
  context.amount > 0 && context.amount <= 500 &&
  resource.dpd <= 30 &&
  resource.priorReliefs < 2 &&
  !resource.legalHold
};
