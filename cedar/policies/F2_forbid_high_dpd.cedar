// key: F2
// description: Global Forbid - No relief may be offered if dpd exceeds 90
forbid(
  principal,
  action,
  resource is Relief::Loan
)
when {
  resource.dpd > 90
};
