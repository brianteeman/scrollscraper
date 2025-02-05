#!/usr/bin/perl


use strict;
use LWP::Simple;
use HTML::TokeParser;
use CGI;
my $hebcalbase = "https://www.hebcal.com/sedrot";
my $scrollscraperbase = "https://scrollscraper.adatshalom.net";
binmode( STDOUT, "encoding(UTF-8)" );

my @englishBookNames =
  ( "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy" );

my @sedrotNames = (
    "bereshit",
    "noach",
    "lech-lecha",
    "vayera",
    "chayei-sara",
    "toldot",
    "vayetzei",
    "vayishlach",
    "vayeshev",
    "miketz",
    "vayigash",
    "vayechi",
    "shemot",
    "vaera",
    "bo",
    "beshalach",
    "yitro",
    "mishpatim",
    "terumah",
    "tetzaveh",
    "ki-tisa",
    "vayakhel",
    "pekudei",
    "vayikra",
    "tzav",
    "shmini",
    "tazria",
    "metzora",
    "achrei-mot",
    "kedoshim",
    "emor",
    "behar",
    "bechukotai",
    "bamidbar",
    "nasso",
    "behaalotcha",
    "shlach",
    "korach",
    "chukat",
    "balak",
    "pinchas",
    "matot",
    "masei",
    "devarim",
    "vaetchanan",
    "eikev",
    "reeh",
    "shoftim",
    "ki-teitzei",
    "ki-tavo",
    "nitzavim",
    "vayeilech",
    "haazinu",
    "vezot-haberakhah",
    "vayakhel-pekudei",
    "tazria-metzora",
    "achrei-mot-kedoshim",
    "behar-bechukotai",
    "chukat-balak",
    "matot-masei",
    "nitzavim-vayeilech",
);

my %englishBookName2Number;
my %sedrotNames;



my $book = 1;
foreach my $bookName (@englishBookNames) {
     $englishBookName2Number{$bookName} = $book++;
}

foreach (@sedrotNames) {
     $sedrotNames{$_}++;
}

my $q = new CGI;
my $parsha;
if ($q->param('parsha')) {
	print "Content-type: text/html\n\n";
	$parsha = $q->param('parsha');
} else {
	$parsha = shift or die "Missing param";
}
die "Invalid parameter" unless $parsha =~ /^\w{1,30}$/;

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(verify_hostname => 0,
              SSL_verify_mode => 0x00);
my $content;



print "The content below has been derived from Hebcal.com, and the links have been modified to point to the ScrollScraper tikkun readings.\n";
print "The unadulterated version of this web page appears <a href=\"";
	
if ($parsha eq "MASTER") {
	my $url = "$hebcalbase/";

	print "$url\">here</a>.<hr>\n";
        my $response = $agent->get($url) or die "Unable to fetch $url";

        $content = $response->decoded_content;
	my @lines = split /[\r\n]+/,$content;

	foreach (@lines) {
		chomp;
		if (/^(<dt>.*href=\")(.*)(\.html)(\".Parashat)/) {
			print "$1$scrollscraperbase/sedrot.cgi?parsha=$2$4\n";
		} elsif (/^(<li>.*href=\")(.*)(\.html)?(\".Parashat)/) {
			print "$1$scrollscraperbase/sedrot.cgi?parsha=$2$4 $2\n";
		} elsif (/^(<li>.*href=\")(.*)\"(.*)/ && defined $sedrotNames{$2}) {
			print "$1$scrollscraperbase/sedrot.cgi?parsha=$2\"$3\n";
		} else {
			print "$_\n";
		}
	}
} else {
	my $url = "$hebcalbase/$parsha.html";

	print "$url\">here</a>.<hr>\n";
        my $response = $agent->get($url) or die "Unable to fetch $url";

        $content = $response->decoded_content;
	my @lines = split /[\r\n]+/,$content;

	foreach (@lines) {
		chomp;
		if (/^(.*title=\")(Audio from ORT\")/) {
			print "$1Tikkun text from ScrollScraper\"\n";
		} elsif (/^(.*title=\")(Hebrew-English bible text\")/) {
			print "$1Tikkun text from ScrollScraper\"\n";
		} elsif (/(^.*href=\")([^\"\/]+)\.html(\".*$)/) {
			print "$1$scrollscraperbase/sedrot.cgi?parsha=$2$3\n";
		} elsif (/^href=\"http.*bible.ort.org.*book=(\d)(.*\">)(\S+ )?([0-9\:\-]*)/ || /^href=\"http.*www.mechon-mamre.org\/p\/pt\/pt0(\d)(.*\">)(\S+ )?([0-9\:\-]*)/) {
			my $book = $1;
			my $optionalBookTitle = $3;
			my $range = $4;
			my ($startc,$startv,$endc,$endv);
			if ($range =~ /^(\d+):(\d+)-(\d+):(\d+)/) {
				$startc = $1;
				$startv = $2;
				$endc = $3;
				$endv = $4;
			} elsif ($range =~ /^(\d+):(\d+)-(\d+)/) {
				$startc = $1;
				$startv = $2;
				$endc = $startc;
				$endv = $3;
			}
			if ($startc) {
				print "href=\"$scrollscraperbase/scrollscraper.cgi?doShading=1&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv\">$optionalBookTitle$range</a>\n";
			} else {
				print "$_\n";
			}
		} elsif (/(.*)<a title="[^"]*".* href=\"https:\/\/www.sefaria.org\/(Genesis|Exodus|Leviticus|Numbers|Deuteronomy)\.(\d+)\.(\d+)-(\d+\.)?(\d+).*<\/a>(.*)/) {
			my $prefix = $1;
			my $suffix = $7;
			my $bookTitle = $2;
			my $book = $englishBookName2Number{$bookTitle};
			my ($startc,$startv,$endc,$endv);
			$startc = $3;
			$startv = $4;
			$endc = $5 || $startc;
			$endv = $6;
			$endc =~ s/\.//g;
			my $range = "$startc:$startv-$endc:$endv";
			if ($startc) {
				print "${prefix}<a title=\"Tikkun text from ScrollScraper\" href=\"$scrollscraperbase/scrollscraper.cgi?doShading=1&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv&trueTypeFonts=0\">$bookTitle $range</a>${suffix}\n";
			} else {
				print "$_\n";
			}
		} else {
			print "$_\n";
		}
	}
}
