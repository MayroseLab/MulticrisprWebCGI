#!/usr/bin/perl
 
 
#print "$ARGV[0]\n";

 
$to = $ARGV[0];
$jobId = $ARGV[1];
$from = 'evolseq@tauex.tau.ac.il';
$subject = 'Your MultiCRISPR job is being processed';

$resultsLink = 'http://multicrispr.tau.ac.il/results.html?jobId=';
$resultsLink = $resultsLink."$jobId";

$message = 'Thanks you for using MultiCRISPR. Your MultiCRISPR job is being processed. We will email you again when processing will finish. View your job\'s progress and results here:';
$message = $message."$resultsLink";
 
open(MAIL, "|/usr/sbin/sendmail -t");
 
# Email Header
print MAIL "To: $to\n";
print MAIL "From: $from\n";
print MAIL "Subject: $subject\n\n";

# Email Body
print MAIL $message;

close(MAIL);
print "Email Sent Successfully to: $to\n";

