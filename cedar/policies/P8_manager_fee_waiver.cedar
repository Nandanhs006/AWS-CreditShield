// key: P8
// description: Manager may waive late fees up to 2000 when dpd <= 60 and prior reliefs < 3
permit(
  principal == Relief::Manager::"manager-tier",
  action == Relief::Action::"OfferFeeWaiver",
  resource is Relief::Loan
)
when {
  context.amount > 0 && context.amount <= 2000 &&
  resource.dpd <= 60 &&
  resource.priorReliefs < 3 &&
  !resource.legalHold
};
