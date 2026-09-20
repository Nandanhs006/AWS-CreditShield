// key: F3
// description: Global Forbid - No relief may be offered if prior reliefs count is 3 or more
forbid(
  principal,
  action,
  resource is Relief::Loan
)
when {
  resource.priorReliefs >= 3
};
