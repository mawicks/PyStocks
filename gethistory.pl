#!/usr/pkg/bin/perl

use LWP::UserAgent;
use Date::Parse;
use DBI;

my $ua = new LWP::UserAgent;
$ua->timeout(5);
$ua->env_proxy;
# $ua->show_progress(TRUE);

# Google adjusts all of the prices for splits, but
# some web reports say they don't adjust for dividends.
# Examining stock prices on dividend dates seems to confirm this.
# Yahoo's adjusted price and Google's adjusted
# prices do not agree and Yahoo clearly claims to adjust both for stock splits
# and dividends. 
#
# Google doesn't explain what they do, and not having actual prices
# and not having dividend adjustments makes Google's historical data
# less useful than Yahoo's.  Yahoo's updates their data later in the 
# evening than Google.
#
# Note: Because of stock splits and dividends, prices must be back adjusted.
# In other words, "historical" prices downloaded today will change because
# of future dividends.  Yahoo provides raw data, so user adjustment is possible.
# Yahoo's data also makes it possible to determine the dates of dividends
# and stock splits.

# For the time being, Yahoo is preferable.  However, here is how the Google
# URLs are formed:

#$url_base = "http://finance.google.com/finance/historical";
#$url_symbol_query = "q=Goog";
#$url_date_range = "startdate=2011-01-01";
#$url = "$url_base?$url_symbol_query&$url_date_range&output=csv";


# Synopsis:    updateHistory symbol startDate endDate
# Description: Generates a url to download stock history from Yahoo
# from startDate to endDate inclusive.

sub historyURL { 	# (symbol, startdate, enddate)
        
    my $urlBase = "http://ichart.finance.yahoo.com/table.csv";
    my ($symbol,$startDate,$endDate) = @_;
    my $urlSymbolQuery = "s=$symbol";
    my $urlDateRange = "";
    if ($startDate) {
	my ($sDay,$sMonth,$sYear) = (strptime($startDate))[3,4,5];
	# strptime produces months ranging from 0-11, days from 1, years relative to 1900.
	#    a=0&b=1&c=2011&d=2&e=12&f=2011&g=d";
	$urlDateRange = $urlDateRange.'a='.$sMonth.'&b='.$sDay.'&c='.($sYear+1900);
    }
    if ($endDate) {
	my $eDay,$eMonth,$eYear;
	($eDay,$eMonth,$eYear) = (strptime($endDate))[3,4,5];
	$urlDateRange = $urlDateRange.'&d='.$eMonth.'&e='.$eMDay.'&f='.($eYear+1900);
    }

    $urlBase.'?'.$urlSymbolQuery.'&'.$urlDateRange.'&g=d&ignore=.csv';
}


$dbh = DBI->connect('dbi:Pg:dbname=stocks', '', '', {AutoCommit=>1});

$searchSymbols = $dbh->prepare("SELECT id FROM symbols WHERE symbol = ?");



# Synopsis:  $symbolID = getSymbolID ("foo");
sub getSymbolID {
    my ($symbol) = @_;
    $searchSymbols -> execute ($symbol) || die ("getSymbolID(): Query failed.");
    $result = $searchSymbols -> fetch;
    $$result[0];
}

$searchHistory = $dbh->prepare("SELECT symbol_id,date FROM history".
                                    " WHERE symbol_id = ? ".
                                    " AND date = ? ");

$insertHistory= $dbh->prepare("INSERT INTO history ".
                                "(symbol_id,date,high,low,open,close,volume,adjustment,source)".
                                " VALUES (?,?,?,?,?,?,?,?,'Yahoo!')");
sub updateDB {
    my $record = $_[0];
    $searchHistory->execute ($record->{symbolID},$record->{date});
    $result = $searchHistory->fetch;
    if (@$result != 0) {
	print "Warning: Record for symbolID=$record->{symbolID}, date=$record->{date} already exists.\n";
    } else {
	$insertHistory->execute($record->{symbolID},
				$record->{date},
				$record->{high},
				$record->{low},
				$record->{open},
				$record->{close},
				$record->{volume},
				$record->{adjustment}) || die ("updateDB(): Insertion failed symbolId=$record->{symbolID},date=$record->{date}");
    }
}

# Synopsis:  updateSymbolHistory symbol previousUpdateDate endDate
# Note: previousUpdateDate must precede endDate and should be a trading day.
# Closing prices for days after "previousUpdateDate" will be downloaded and stored,
# but prices on "previousUpdateDate" will not.  The values from "previousUpdateDate"
# are used to determine whether the closing price was adjusted on
# following trading day due to dividends or stock splits, but not saved in the
# database.  Presumably theses values were saved earlier.

$updateLatestHistoryDate = $dbh->prepare("UPDATE symbols SET latest_history_date=? ".
                                       "WHERE id=?");
$updateEarliestHistoryDate = $dbh->prepare("UPDATE symbols SET earliest_history_date=? ".
                                       "WHERE id=?");
$getHistoryRange = $dbh->prepare("SELECT earliest_history_date,latest_history_date ".
				  "FROM symbols WHERE id=?");

sub getHistoryRange {
    my ($symbolID) = @_;
    $getHistoryRange->execute($symbolID) || die ("getHistoryRange() Select failed.\n");
    $result = $getHistoryRange->fetch;
    $result
}

my $nupdates = 0;

sub updateSymbolHistory {
    my ($symbol) = @_;
    my $symbolID = getSymbolID ($symbol);
    my ($previousEarliestDate,$previousLatestDate) = @{getHistoryRange ($symbolID)};

    $url = historyURL($symbol, $previousLatestDate);

    $nupdates = $nupdates + 1;
    print "$nupdates) Downloading $symbol from ".
           ($previousLatestDate?$previousLatestDate:"the beginning")." to today...";
    my $response = $ua->get($url);
    if (($response->is_error)) {
	print "Error: ",$response->status_line,"\n";
	print "*** Skipping symbol $symbol ***\n";
    }
    else {
	my$content = $response->decoded_content((ref=> TRUE));
    
	my @lines = split /^/m, $$content;
    
	my $recordNumber = 0;
	my $recordsImported = 0;
	my %previous;
	
	foreach $line (@lines)
	{
	    $recordNumber += 1;
	    chomp $line;
	    my ($date,$open,$high,$low,$close,$volume,$adjustedClose) = split /,/, $line;
	    print "Date: $date, close: $close\n";
	    # Skip header...
	    if ($recordNumber == 1) {
		next;
	    }
	    
	    my ($ss,$mm,$hh,$day,$month,$year) = strptime($date);
	    my $formattedDate = "@{[$year+1900]}-@{[$month+1]}-@{[$day]}";
	    print "formattedDate=$formattedDate\n";
	    %current = (symbolID=>$symbolID,
		date=>$formattedDate,
		open=>$open,
		high=>$high,
		low=>$low,
		close=>$close,
		volume=>$volume,
		adjustedClose=>$adjustedClose);
	    
	    if (%previous) {
		# Here "previous" referes to the file, not time.  "Previous" values are actually more recent.
		$adjustment = $current{close} - $previous{close}*$current{adjustedClose}/$previous{adjustedClose};
		$absadjustment = int(100*abs($adjustment)+0.5)/100.0;
		$previous{adjustment} = ($adjustment>0? $absadjustment: -$absadjustment) if (abs($adjustment)>.015);
		updateDB (\%previous);
		$recordsImported += 1;
		$earliestDate = $previous{date};
	    } else {
		$latestDate = $formattedDate;
	    }
	    %previous = %current;
	}
	
	printf "Updating history record for $symbolID to $latestDate\n";
	$updateLatestHistoryDate->execute ($latestDate,$symbolID) || die ("Error updating last history date in symbols table\n");
	if (!$previousEarliestDate) {
	    $updateEarliestHistoryDate->execute ($earliestDate,$symbolID) unless ($previousEarliestDate);
	}
	print "${recordsImported} record";
	print "s" unless ($recordsImported == 1);
	print "\n";
	if ($recordsImported > 0) {
	    print "Adjusting closing prices for $symbol...";
	    adjustClosingPrices($symbolID);
	    print "done.\n"
	}
    }
}
    
# Synopsis:  adjustClosingPrices symbolID
# Recalculates and updates the historical closing prices as well as the
# daily returns.

$getHistoryRecords = $dbh->prepare("SELECT date,close,adjustment ".
                                     "FROM history ".
                                    "WHERE symbol_id=? ".
                                 "ORDER BY date DESC");

$updateHistoryRecords = $dbh->prepare("UPDATE history ".
                                      "SET adjusted_close=?,".
                                          "daily_return=? ".
                                    "WHERE symbol_id=? ".
                                      "AND date=?");
sub adjustClosingPrices {
    my ($symbolID) = @_;
    $getHistoryRecords->execute($symbolID);
    my ($close, $adjustment,$adjustedClose,$dailyReturn);
    my %previous;
    $getHistoryRecords->bind_columns(\$date, \$close, \$adjustment);
    while ($result = $getHistoryRecords->fetch) {
        if (%previous) {
	    $adjustedClose = $previous{adjustedClose}*($close-$previous{adjustment})/$previous{close};
	    $previous{dailyReturn} = log($previous{adjustedClose}) - log($adjustedClose);
	    $updateHistoryRecords->execute($previous{adjustedClose},
					   $previous{dailyReturn},
					   $symbolID,$previous{date}) || die;
        } else{
	    $adjustedClose = $close;
	}
	$previous{date} = $date;
	$previous{close} = $close;
	$previous{adjustment} = $adjustment;
	$previous{adjustedClose} = $adjustedClose;
    }
    $updateHistoryRecords->execute($adjustedClose,0.0, $symbolID,$date);
}

$getWatchList = $dbh->prepare("SELECT symbol FROM symbols s,watch_list w ".
                              "WHERE s.id = w.symbol_id ".
			      "AND (s.latest_history_date < (CURRENT_DATE-1) OR ".
			      "     s.latest_history_date is null )" );

sub updateWatchListHistory {
    $getWatchList->execute || die;
    
    while ($result = $getWatchList->fetch)
    {
	updateSymbolHistory($result->[0]);
    }
}


updateWatchListHistory;

# print Dumper($content);
