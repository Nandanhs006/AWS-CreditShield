// key: P6
// description: Manager may extend tenure up to 6 months when dpd <= 60 and prior reliefs < 2
permit(
  principal == Relief::Manager::"manager-tier",
  action == Relief::Action::"OfferTenureExtension",
  resource is Relief::Loan
)
when {
  context.months > 0 && context.months <= 6 &&
  resource.dpd <= 60 &&
  resource.priorReliefs < 2 &&
  !resource.legalHold
};
