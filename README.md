# tap-dmarcian

This tap assumes that you have set up [Dmarcian](https://dmarcian.com) automated Data Export emails daily, and sent to [an email address which can put data in an S3 bucket](https://aws.amazon.com/premiumsupport/knowledge-center/ses-receive-inbound-emails/), and [a service extracts attachments from the `.eml` files](https://git.fixdapp.com/core/email-to-s3) in a particular naming convention.

This tap simply reads the attachments from S3 and passes that data along. This tap is very particular to our use case and unlikely to be of any value to other parties. However, the terms of AGPL compel us to publish it publicly.

https://dmarcian.com/explanation-of-csv-columns-in-data-exports/

---

Copyright &copy; 2021 FIXD Automotive, Inc.
