## Checkout & Payments
- Completed the new guest checkout flow — shipped to 100% of users on Tuesday
- Fixed critical bug where promo codes were silently failing for international users (affected ~800 users/day)
- Still working on Apple Pay integration; backend is ready, waiting on frontend team to finish the UI component
- Performance regression in payment confirmation page (P99 went from 200ms to 1.2s after last week's deploy) — root cause identified, fix is in review
- Next week: deploy Apple Pay, investigate and fix the P99 regression, start planning for Stripe webhook retry logic

## Platform & Infrastructure
- Completed Postgres 15 → 16 migration for the main product database with zero downtime
- Kubernetes cluster autoscaling tuned — reduced idle node costs by ~23% month-over-month
- Blocked on security review for the new S3 bucket policy needed for the document storage feature; submitted request 2 weeks ago, no response from InfoSec yet
- Oncall had 3 pages this week: 2 were noise (fixed alert thresholds), 1 was a real disk-space issue on the logging cluster (resolved)
- Next week: finalize observability stack upgrade (Prometheus 2.48), follow up with InfoSec on S3 policy

## Data & Analytics
- Launched new self-serve reporting dashboard for internal business teams — 47 users in first 3 days
- ETL pipeline refactor is 60% complete; reduced average pipeline run time from 4.2 hours to 1.8 hours so far
- Dependency: need final schema from the Payments team for the new revenue attribution model — this is blocking the Q4 analytics roadmap
- Discovered data quality issue in the customer cohort table (duplicate rows from a backfill in August); investigating scope and fix
- Next week: finish ETL refactor, resolve data quality issue, start design doc for real-time event streaming

## Mobile (iOS & Android)
- iOS 4.2 release submitted to App Store — under review, expected to go live Thursday or Friday
- Android team resolved the ANR issue that was causing 0.3% crash rate on older devices; shipped in hotfix 4.1.3
- Push notification deliverability dropped from 94% to 87% after Firebase SDK upgrade; Firebase support ticket open, investigating
- Sprint planning for Q4 features completed; roadmap alignment meeting with Product scheduled for next Tuesday
- Next week: monitor iOS 4.2 launch, resolve push notification issue, kick off Q4 sprint 1
