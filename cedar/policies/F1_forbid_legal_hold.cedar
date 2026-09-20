// key: F1
// description: Global Forbid - No relief may be offered if account is under legal hold
forbid(
  principal,
  action,
  resource is Relief::Loan
)
when {
  resource.legalHold == true
};
