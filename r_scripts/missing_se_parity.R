suppressPackageStartupMessages(library(jsonlite))
args <- commandArgs(trailingOnly = TRUE)
in_path <- args[1]
out_path <- args[2]
dat <- fromJSON(in_path)
z <- qnorm(1 - dat$p_value / 2)
se_A <- abs(dat$effect) / z
se_B <- (dat$ci_upper - dat$ci_lower) / (2 * qnorm(0.975))
writeLines(toJSON(list(A = se_A, B = se_B), auto_unbox = TRUE), out_path)
