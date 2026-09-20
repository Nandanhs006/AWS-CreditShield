// key: P2
// description: Manager may approve shift up to 30 days when dpd <= 60 and prior reliefs < 3
permit(
  principal == Relief::Manager::"manager-tier",
  action == Relief::Action::"OfferDueDateShift",
  resource is Relief::Loan
)
when {
  context.days > 0 && context.days <= 30 &&
  resource.dpd <= 60 &&
  resource.priorReliefs < 3 &&
  !resource.legalHold
};
