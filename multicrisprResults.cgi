#!/usr/bin/perl -w

use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use JSON;
use File::Slurp;
use List::Util qw(first);
use List::MoreUtils qw(any  first_index);

use lib "/bioseq/multicrispr";

#use lib "/bioseq/bioSequence_scripts_and_constants";
use lib "../";
use multicrispr_CONSTS_and_Functions;

my $query = new CGI;
my $jobId = $query->param('jobId');
my $removeRepetitions = $query->param('removeRepetitions');

my %jsonData;
$jsonData{'errorOccured'} = 0;
$jsonData{'jobId'} = $jobId;

# checking if jobId is valid
if (!($jobId =~ /^[0-9]+\z/))
{
	$jsonData{'errorOccured'} = 1;
	$jsonData{'error'} = "Job $jobId contains invalid characters";
}
else
{
	my $curJobDir = multicrispr_CONSTS_and_Functions::RESULTS_LINK."/$jobId";
	
	# checking if job directory exists
	if (-d $curJobDir)
	{
		my $dataResultsRef = &GetResultsData($jobId, $curJobDir);
		my %dataResults = %$dataResultsRef;
		
		%jsonData = (%jsonData, %dataResults);
   
	}
	else
	{
		$jsonData{'errorOccured'} = 1;
	    $jsonData{'error'} = "Job $jobId does not exists.";
	}
}


# parsing return data to json and returnig it to client
my $json = encode_json(\%jsonData);
print $query->header();
print "$json\n";

sub GetResultsData
{
	my ($jobId, $curJobDir) = @_;
	
	my %jsonData;
	
	$jsonData{'jobId'} = $jobId;
	
	$jsonData{'jobStatus'} = &GetJobStatus($jobId, $curJobDir);
	
	#$jsonData{'jobType'} = &GetJobType($curJobDir);
	
	$jsonData{'files'} = &GetOutputFiles($curJobDir);
	
	#$jsonData{'images'} = &GetOutputImages($curJobDir);
	
	my $logText = &ReadFromFile("$curJobDir/".multicrispr_CONSTS_and_Functions::LOG_FILE, "");
	$jsonData{'logText'} = $logText;

	my $outText = &ReadFromFile("$curJobDir/".multicrispr_CONSTS_and_Functions::OUTPUT_FILE, "");
	$jsonData{'outText'} = $outText;

	#$jsonData{'jobTitle'} 		= &ReadFromFile("$curJobDir/title", "");
	#$jsonData{'algType'} 		= &ReadFromFile("$curJobDir/alg", "");
	$jsonData{'params'} 		= &ReadFromFile("$curJobDir/".multicrispr_CONSTS_and_Functions::FILENAME_PARAMS, "");
	#$jsonData{'fname_resultTree'}	 	= "$curJobDir/".multicrispr_CONSTS_and_Functions::FILENAME_RESULT_TREE;
 
  my $table;

  if ($removeRepetitions) {
	$table = &ReadFromFile("$curJobDir/"."removed_repetitions_table.html", "");
  }
  else {
	$table = &ReadFromFile("$curJobDir/"."the_table.html", "");
	}
	
  $jsonData{'resultTable'} = $table;
 
  my $table2 = &ReadFromFile("$curJobDir/"."cover_table.html", "");
  $jsonData{'resultTableCover'} = $table2;
 # $jsonData{'resultTable'} = "$curJobDir/result_table"; #Shlomtzion!!!!!
  
  if (-e "$curJobDir/".multicrispr_CONSTS_and_Functions::RESULT_TREE)
  {
    $jsonData{'linkTree'} = "<a href=\"".multicrispr_CONSTS_and_Functions::SERVER_LINK."/PhyD3/view_tree.php?id=".$jobId."&f=newick\"target=\"_blank\">View Genes Tree</a>"; #Shlomtzion
  }
  
#  <a href="/images/myw3schoolsimage.jpg" download>
#  <img border="0" src="/images/myw3schoolsimage.jpg" alt="W3Schools" width="104" height="142">
#</a>
  $jsonData{'download'} = "<a href=\"$curJobDir/CRISPys_output.csv\" download><span class=\"glyphicon glyphicon-download-alt\"></span> Download</a>"; #Shlomtzion

	#my $paramsText = &ReadFromFile("$curJobDir/".multicrispr_CONSTS_and_Functions::LOG_FILE	, "");
	#my $paramsText = &ReadFromFile("$curJobDir/title", "");
	#my $paramsText = "OFER paramsText";
	#$jsonData{'paramsText'} = $paramsText;
	
	return \%jsonData;
}

sub GetOutputFiles
{
	my ($curJobDir) = @_;
	
	my @filesDict;
	
	#my $filename = "$curJobDir/".multicrispr_CONSTS_and_Functions::OUTPUT_FILES_LIST;
	 
	#my @files = &ReadFromFile($filename);
	my @files = multicrispr_CONSTS_and_Functions::OUTPUT_FILE;
	#$files[0] = $curJobDir/ ".ofer";
	
	foreach my $file (@files)
    {
			$file =~ s/^\s+//;
			$file =~ s/\s+$//;
			
 			my %curFile;
 			$curFile{'name'} = $file;
 			$curFile{'path'} = "$curJobDir/$file";
 			
 			push (@filesDict, \%curFile);
	}
	 
    return \@filesDict;
}

#sub GetOutputImages
#{
#	my ($curJobDir) = @_;
#	
#	my @imagesDict;
#	
#	my $filename = "$curJobDir/".multicrispr_CONSTS_and_Functions::IMAGES_TO_DISPLAY_LIST;
#	 
#	my @lines = &ReadFromFile($filename);
#	
#	foreach my $line (@lines)
#   {
#			$line =~ s/^\s+//;
#			$line =~ s/\s+$//;
#			
#			my @parts = split("\t", $line);
#
#			my $file = pop(@parts);
#			my $url = "$curJobDir/$file";
#			
#			
# 			my %curImg;
#			$curImg{'titleParts'} = \@parts;
# 			$curImg{'url'} = $url;
# 			
#			push (@imagesDict, \%curImg);
#	}
#	 
#   return \@imagesDict;
#}

#sub GetJobType
#{
#	my ($curJobDir) = @_;
#	
#	my $jobTypeFile = "$curJobDir/".multicrispr_CONSTS_and_Functions::JOB_TYPE_FILE;
#	
#	my $jobType = &ReadFromFile($jobTypeFile,'unknown');
#	
#	return $jobType;
#}

sub GetJobStatus
{
	my ($jobId, $curJobDir) = @_;
	
	if (&ReadErrorLogFileStatus($curJobDir))
	{
		return 'error';
	}
	else {
		my $jobNumFile = "$curJobDir/".multicrispr_CONSTS_and_Functions::QSUB_JOB_NUM_FILE;
		
		my $qsubJobNum = &ReadFromFile($jobNumFile, 0);
		
		if ($qsubJobNum eq "validating") {
			return "validating input files";
		}
		elsif ($qsubJobNum) 
	 	{
			#my $qstatCmd = 'ssh bioseq@lecs2 qstat';
			#my $qstatCmd = 'ssh bioseq@jekyl qstat';
			my $qstatCmd = 'ssh bioseq@powerlogin qstat -s';
			my $qstatCmdResponse = `$qstatCmd`;	
			
			my @responseLines = split("\n", $qstatCmdResponse);
			
			if (!any { /$qsubJobNum/ } @responseLines)
			{
					return 'finished';
			}
			else
			{
				my $jobNumLine = first { /$qsubJobNum/ } @responseLines;
			
				my @jobNumLines = split(" ",$jobNumLine);
				
				my $jobStatus = $jobNumLines[9]; #$jobNumLines[4]
				
				$jobStatus = lc($jobStatus);
				
				if (index($jobStatus, 'e') != -1)
				{
		    		return 'error';
				}
				elsif (index($jobStatus, 'r') != -1 || index($jobStatus, 't') != -1)
				{
					return 'running';
				}
				elsif (index($jobStatus, 'q') != -1 || index($jobStatus, 'w') != -1)
				{
#					my $log = "$curJobDir/".multicrispr_CONSTS_and_Functions::LOG_FILE;
#					&WriteToFileWithTimeStamp($log, "Job $jobId is waiting in queue.");
#					
					return 'waiting in queue';
				}
				elsif (index($jobStatus, 'c') != -1)
				{
					return 'finished';
				}
				else
				{
					return $jobStatus;
				}
			}
	 	}
	}
	
 	return 'unknown';
}

sub ReadErrorLogFileStatus
{
	my ($curJobDir) = @_;
	
	my $errLog = "$curJobDir/".multicrispr_CONSTS_and_Functions::ERROR_STATUS_LOG_FILE;

	my $errStatus = ReadFromFile($errLog, 0);
	
	return $errStatus;
}



