suppressPackageStartupMessages({
  library(metafor)
  library(jsonlite)
})
args <- commandArgs(trailingOnly = TRUE)
in_path <- args[1]
out_path <- args[2]
dat <- fromJSON(in_path)
fit <- rma(yi = dat$estimate, sei = dat$se, method = "REML")
writeLines(
  toJSON(
    list(
      mu = as.numeric(fit$b),
      mu_se = as.numeric(fit$se),
      tau = sqrt(fit$tau2)
    ),
    auto_unbox = TRUE
  ),
  out_path
)
