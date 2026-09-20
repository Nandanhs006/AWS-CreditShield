// key: P1
// description: Agent may shift due date up to 10 days when dpd <= 30 and prior reliefs < 2
permit(
  principal == Relief::AiAgent::"agent-v1",
  action == Relief::Action::"OfferDueDateShift",
  resource is Relief::Loan
)
when {
  context.days > 0 && context.days <= 10 &&
  resource.dpd <= 30 &&
  resource.priorReliefs < 2 &&
  !resource.legalHold
};
