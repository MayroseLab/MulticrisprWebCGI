#!/usr/bin/perl -w

use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use File::Basename;
use File::Path; 
use File::Slurp;
#use Captcha::reCAPTCHA;
#use File::Copy qw(move);
use lib "../";
use lib "/bioseq/multicrispr";

use multicrispr_CONSTS_and_Functions;

use CGI::Fast qw(:standard);
use Captcha::reCAPTCHA::V2;

# this command limits the size of the uploded file
my $maxMB = 100; 
$CGI::POST_MAX = 1024 * 1000 * $maxMB;

my $safe_filename_characters = "a-zA-Z0-9_.-";
my $jobId 			= $^T;
my $curJobdir 		= multicrispr_CONSTS_and_Functions::RESULTS_DIR_ABSOLUTE_PATH."$jobId";
my $log 			= "$curJobdir/".multicrispr_CONSTS_and_Functions::LOG_FILE;
#my $fnameTitle 		= "$curJobdir/title";
#my $fnameAlg 		= "$curJobdir/alg";
my $fnameFasta 		= "$curJobdir/user.fasta";
my $fnameParams		= "$curJobdir/".multicrispr_CONSTS_and_Functions::FILENAME_PARAMS;
my $errLog 			= "$curJobdir/".multicrispr_CONSTS_and_Functions::ERROR_STATUS_LOG_FILE;

#my $query = new CGI;

while(my $query = new CGI::Fast) {

  if( request_method eq 'POST' ) {

	# commented out captcha code
    #my $rc = Captcha::reCAPTCHA::V2->new;
    #my $result = $rc->verify('6LdCZJ0UAAAAAHnPG6Vv9jd1ZzAaP7Y1H1-FI8mb', param('g-recaptcha-response'), remote_host);

    # Check the result
    #if( !$result->{success} ){
      # The check failed, ignore the POST
    #  next;
    #}

    # Do something with the form



	# getting inputs from user

	# copy the seq from textarea to file
	my $fasta					= $query->param("inputText");
	if (!($fasta eq ""))
	{
		&WriteToFile( $fnameFasta, $fasta);
	}

	my $inputFile				= $query->param("inputFile");
	my $email_to_address		= $query->param("inputEmail");
	#my $algType					= $query->param("algType");
	my $homology;
	if ($query->param("homology") eq "on")
	{
	  $homology        = $query->param("homology");
	}
	else {$homology        = "off"}
	my $funcType				= $query->param("funcType");
	my $useThreshold    = $query->param("useThreshold");
	my $threshold;
	if ($useThreshold eq "yes")
	{
	  $threshold				= $query->param("threshold");
	}
	else { $threshold = $useThreshold}
	my $jobTitle				= $query->param("jobTitle");
	my $pam = $query->param("pam");
	my $genomeAssembly = $query->param("genomeAssembly");

	if ($funcType eq "Azimuth") {$funcType = "CFD score";}
	#&WriteToFile( $fnameParams, "<h4>Job Title: <i>".$jobTitle."</i></h4><h4>Scoring Function: <i>".$funcType."</i></h4><h4>Consider homology: <i>".$homology."</i></h4><h4>Threshold: <i>".$threshold."</i></h4><h4>PAM sequence: <i>".$pam."</i></h4><h4>Genome Assembly: <i>".$genomeAssembly."</i></h4><h4>Email: <i>".$email_to_address."</i></h4>");
	&WriteToFile( $fnameParams, "<h4>Job Title: <i>".$jobTitle."</i></h4><h4>Scoring Function: <i>".$funcType."</i></h4><h4>Consider homology: <i>".$homology."</i></h4><h4>Threshold: <i>".$threshold."</i></h4><h4>PAM sequence: <i>".$pam."</i></h4><h4>Genome Assembly: <i>".$genomeAssembly."</i></h4><h4>Email: <i>".$email_to_address."</i></h4>");

	if ($funcType eq "CFD score") {$funcType = "Azimuth";}
	#if ($genomeAssembly eq "No selected"){
	#  $genomeAssembly = "none";
	#}

	if ($pam eq "NGG")
	{ 
	  $pam = 0;
	}
	else {$pam = 1;}


	# creating cur job directory
	mkpath($curJobdir);

	#if ( !$inputFile )
	#{
	#	print $query->header ( );
	#	print "There was a problem uploading your structure zip (try a smaller file).";
	#	exit;
	#} 

	# checking filename for invalid characters
	if ($inputFile)
	{
		my ( $name, $path, $extension ) = fileparse ( $inputFile, '\..*' );
		$inputFile = $name . $extension;
		$inputFile =~ tr/ /_/;
		$inputFile =~ s/[^$safe_filename_characters]//g;

		if ( $inputFile =~ /^([$safe_filename_characters]+)$/ )
		{
			$inputFile = $1;
		}
		else
		{
			die "Filename contains invalid characters";
		}		
		
		# uploading file to job directory
		my $upload_filehandle = $query->upload("inputFile");
		my $serverLocation = "$curJobdir/$inputFile";
		open ( UPLOADFILE, ">$serverLocation" ) or die "$!";
		binmode UPLOADFILE;

		while ( <$upload_filehandle> )
		{
			print UPLOADFILE;
		}

		close UPLOADFILE;

		rename $serverLocation, $fnameFasta;
		#my $cmd = "mv $serverLocation $fnameFasta";
		#&WriteToFileWithTimeStamp($log, "cmd: $cmd");
		#`$cmd`;
	}

	# building perl script command
	my $serverName 		= multicrispr_CONSTS_and_Functions::SERVER_NAME;
	my $pythonModule	= multicrispr_CONSTS_and_Functions::PYTHON_MODULE_TO_LOAD;
	my $perlModule		= multicrispr_CONSTS_and_Functions::PERL_MODULE_TO_LOAD;

	my $pid = fork();
	if( $pid == 0 )
	{
		# this code runs async
		open STDIN,  '<', '/dev/null';
		#open STDOUT, '>', $validationLog; # point to /dev/null or to a log file
		#open STDERR, '>&STDOUT';
		
		# logging user request
		use POSIX qw(strftime);
		my $date = strftime('%F %H:%M:%S', localtime);
		my $logPath = multicrispr_CONSTS_and_Functions::LOG_DIR_ABSOLUTE_PATH; 
		$logPath = $logPath.multicrispr_CONSTS_and_Functions::MAIN_PIPELINE_LOG;
		&WriteToFile( $logPath, "$email_to_address\t$date\t$jobId");

		#creating shell script file for lecs2
		my $qsub_script = "$curJobdir/qsub.sh";
		open (QSUB_SH,">$qsub_script");
		  
		#print QSUB_SH "#!/bin/tcsh\n";
		#print QSUB_SH '#$ -N ', "$serverName"."_$jobId\n";
		#print QSUB_SH '#$ -S /bin/tcsh', "\n";
		#print QSUB_SH '#$ -cwd', "\n";
		#print QSUB_SH '#$ -l bioseq', "\n";
		#print QSUB_SH '#$ -e ', "$curJobdir", '/$JOB_NAME.$JOB_ID.ER', "\n";
		#print QSUB_SH '#$ -o ', "$curJobdir", '/$JOB_NAME.$JOB_ID.OU', "\n";
		
		print QSUB_SH "#!/bin/bash\n";
		print QSUB_SH '#PBS -N ', "$serverName"."_$jobId\n";
		print QSUB_SH "#PBS -r y\n";
		print QSUB_SH "#PBS -q lifesciweb\n";
		print QSUB_SH "#PBS -v PBS_O_SHELL=bash,PBS_ENVIRONMENT=PBS_BATCH\n";
		print QSUB_SH '#PBS -e ', "$curJobdir", '/', "\n";
		print QSUB_SH '#PBS -o ', "$curJobdir", '/', "\n";
		
		print QSUB_SH "cd $curJobdir\n";
		print QSUB_SH "module load $pythonModule\n";
		print QSUB_SH "module load mafft/mafft7149\n";
		print QSUB_SH "module load phylip/3.697\n";	# To enable the protdist cmd which is part of the PHYLIP package
		#print QSUB_SH "module load python/python-anaconda3.5\n";
		print QSUB_SH "module load $perlModule\n";
		print QSUB_SH "hostname;\n"; # for debug - to know which node ran the job	

		#my $cmd .= "python /bioseq/oneTwoTree/buildTaxaTree.py --taxa-list-file taxon_names --working-dir $curJobdir --config-filename /bioseq/multicrispr/ploidb-conf-yoni.ini --cluster-method orthomclits --log-filename $jobId.log --debug-filename $jobId-debug.log --id $jobId ;";
		
		#my $out = $curJobdir."/".multicrispr_CONSTS_and_Functions::OUTPUT_FILES_LIST;
		#my $logfile = $curJobdir."/".$jobId.".log";
		#my $logfile = multicrispr_CONSTS_and_Functions::LOG_FILE;
		
		#my $cmd .= "python /groups/itay_mayrose/galhyams/MULTICRISPER/codeV1.1/call_MULTICRISPR_Wrapper.py $fnameFasta > $logfile";
		#my $myScript = "/groups/itay_mayrose/galhyams/CrispysV1.6_2505/call_MULTICRISPR_Wrapper.py";
		my $myScript = "/bioseq/multicrispr/python/call_MULTICRISPR_Wrapper.py";

	 #fasta_file, path , alg = 'A', where_in_gene = 1, use_thr = 0,  Omega = 1, df_targets = Metric.cfd_funct,
	  my $where_in_gene = 1;
	  my $use_thr = 0;
	  my $Omega = 1;
	  my $use_homology = "A";
	  if ($homology eq "on")
	  {
		$use_homology = "E";
		}
	  if ($threshold eq "no")
	   {$use_thr = 0;
		}
	   
	   else  {
	   $use_thr = 1;
	   $Omega = $threshold;
	   }
	   my $func_type;
	   if ($funcType eq "CRISPR Design")
	   { $func_type ="MITScore";}
	   elsif ($funcType eq "Azimuth")
	   { $func_type ="cfd_funct";}
	   elsif ($funcType eq "CCtop")
	   { $func_type ="ccTop";}
	   
	   
		#my $cmd = "python $myScript $fnameFasta $curJobdir $use_homology $threshold";# $func_type";
	  #fasta_file, path , alg = 'A', where_in_gene = 1, use_thr = 0, Omega = 1, df_targets = Metric.cfd_funct, protodist_outfile = "outfile", min_length= 20, max_length = 20,start_with_G = False, internal_node_candidates = 10, PS_number = 12, PAMs = 1, calculate_off_targets = 0
	  my $min_length = 20;
	  my $max_length = 20; 
	  my $start_with_G = "False";
	  my $internal_node_candidates = 10;
	  my $PS_number = 12;
	  
	  my $cmd = "python $myScript $fnameFasta $curJobdir --alg $use_homology --t $use_thr --v $Omega --s $func_type --PAMs $pam --off_targets $genomeAssembly";
	  #my $cmd = "python3 $myScript $fnameFasta $curJobdir --alg $use_homology --t $use_thr --v $Omega --s $func_type --PAMs $pam --off_targets $genomeAssembly";
	  #my $cmd = "python3 $myScript $fnameFasta $curJobdir --alg $use_homology --t 0 --v 1 --s $func_type --PAMs $pam --off_targets $genomeAssembly";

	  #my $cmd = "python3 $myScript $fnameFasta $curJobdir $use_homology $where_in_gene $use_thr $Omega $func_type outfile $min_length $max_length $start_with_G $internal_node_candidates $PS_number $pam $genomeAssembly";
	  #my $cmd = "python3 $myScript $fnameFasta $curJobdir $use_homology $where_in_gene $use_thr $Omega $func_type";

		
		print QSUB_SH "$cmd\n";
		&WriteToFileWithTimeStamp($log, "cmd: $cmd\n");
		#&WriteToFileWithTimeStamp($log, "params are: inputFile: $inputFile. Job Title: $jobTitle. Scoring Function: $func_type. Consider homology: $homology. Threshold: $threshold. Email: $email_to_address. GenomeAssembly: $genomeAssembly");
	 &WriteToFileWithTimeStamp($log, "params are: inputFile: $inputFile. Job Title: $jobTitle. Scoring Function: $func_type. Consider homology: $homology. Threshold: $threshold. Email: $email_to_address. \n");
		
		#print QSUB_SH "cd $curJobdir\n";
		#my $cmdProtDist = 'echo "/bioseq/data/results/multicrispr/'.$jobId.'/phylip_file.ph\nF\n/bioseq/data/results/multicrispr/'.$jobId.'/protdist_file.ph\nY" | protdist';
		#my $cmdProtDist = 'echo "/bioseq/data/results/multicrispr/'.$jobId.'/phylip_file.ph\nY\n" | protdist';
		#print QSUB_SH "$cmdProtDist\n";
		#&WriteToFileWithTimeStamp($log, "cmdProtDist: $cmdProtDist");
		
		# this will send results ready email to user 
		#my $cmdEmail = "cd /bioseq/multicrispr/;perl sendLastEmail.pl --toEmail $email_to_address --id $jobId --subject 'CRISPys daily test results';";
		#print QSUB_SH "$cmdEmail\n";
		my $cmdWriteDailyTest = "cd /bioseq/multicrispr/python;python write_daily_test.py ".multicrispr_CONSTS_and_Functions::DAILY_TESTS_DIR." $jobId;";
		print QSUB_SH "$cmdWriteDailyTest\n";
		
		close (QSUB_SH);
		
		#my $qsubCmd =  'ssh bioseq@lecs2 qsub '."$qsub_script";
		#my $qsubCmd =  'ssh bioseq@jekyl qsub '."$qsub_script"; #On ibis3
		my $qsubCmd =  'ssh bioseq@powerlogin qsub '."$qsub_script"; 
		&WriteToFileWithTimeStamp($log, "going to execute qsubCmd: $qsubCmd");
		my 	$qsubJobNum = "NONE";
		my $ans = `$qsubCmd`;
		if ($ans =~ /(\d+)/)
		{
			$qsubJobNum = $1;
		}
		
		write_file("$curJobdir/".multicrispr_CONSTS_and_Functions::QSUB_JOB_NUM_FILE, $qsubJobNum);
		&WriteToFileWithTimeStamp($log, "Job $jobId was submitted to queue.");
		&WriteToFileWithTimeStamp($log, "qsubJobNum: $qsubJobNum");
		
		# send 1st email to user
		#`perl sendFirstEmail.pl email_to_address $jobId`;
		
		exit 0;
	}


	# redirecting client to results page
	my $redirectedURL = multicrispr_CONSTS_and_Functions::RESULTS_PAGE_URL."?jobId=";
	$redirectedURL = $redirectedURL.$jobId;
	print $query->redirect($redirectedURL);


		
	

  }


}


