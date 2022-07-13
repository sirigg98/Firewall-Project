# delimit; 
clear all;
set more off;
local rundate "11July22";

local dir "D:\git repo\Firewall-Project\data\Output Files";
cd "`dir'";


use main_papers_v3.dta, clear;
merge 1:1 author_id_paper_id using num_google_site_v3.dta; drop _m;

/*

    Result                           # of obs.
    -----------------------------------------
    not matched                             0
    matched                            97,434  (_merge==3)
    -----------------------------------------

*/

keep if num_auths < 11; /*num obs: 96,382*/

gen share = googlesite/num_auths;
*Clearly bimodal dist, dummy should work well;
hist share;

summ googlesite, det; 
summ num_auths, det;

**  Generating candidating explanatory variables from googlesite;
gen atleastone = (share>0 & share~=.); 
gen nogoogle = (share == 0 & share~=.);
gen allgoogle = (share >=1);
gen somegoogle = (share > 0 & share < 1);

tab allgoogle; /*Only ~4% of papers. Ran the regs with this, and the results were quite underpowered*/
tab somegoogle;

* The median paper has only one top50 authors on it (the author who's profile the paper was extracted from). num_top50 == 0 since this is a count of the top50 authors in the coauthors variable;
gen one_top50 = (num_top50 == 0);

merge 1:n author_id_paper_id using "citations_v3.dta"; drop if _m != 3; drop _m;

/*

    Result                           # of obs.
    -----------------------------------------
    not matched                       517,658
        from master                         0  (_merge==1)
        from using                    517,658  (_merge==2)

    matched                         1,266,079  (_merge==3)
    -----------------------------------------
_merge == 2 is not 0 since citations_v3.dta are the citation counts for all the papers in our dataset (144k papers, before deduplication). 
*/


gen dum2010 = (year >= 2010);
bysort author_id_paper_id (year): gen cum_cites = sum(citation_count);
sort author_id_paper_id year;
bysort author_id_paper_id: egen min_year=min(year);
gen paper_age = 1 if year==min_year;
replace paper_age = 1 + (year-min_year);

egen panelid = group(author_id_paper_id);
xtset panelid year;

**** Delimiters not used after this point to run line-by-line;

************************************* Results for prelim regs table *************************************

local ofile "prelim_regs_v3_ols"
***** Table 1: OLS
** Column I: Baseline
reghdfe citation_count  c.dum2010##c.atleastone c.dum2010##c.desc_ref_china  i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") replace
** Column II: Baseline + num_auths x D(year)
reghdfe citation_count  c.dum2010##c.atleastone c.dum2010##c.desc_ref_china i.year#c.num_auths i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") append
** Column III: Add triple interaction with only one top50 author on paper		
reghdfe citation_count  c.dum2010##c.atleastone##c.one_top50 c.dum2010##c.desc_ref_china i.year#c.num_auths  i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") append

***** Table 1: PPML
** Column I: Baseline
local ofile "prelim_regs_v3_ppml"
ppmlhdfe citation_count  c.dum2010##c.atleastone c.dum2010##c.desc_ref_china  i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") replace
** Column II: Baseline + num_auths x D(year)
ppmlhdfe citation_count  c.dum2010##c.atleastone c.dum2010##c.desc_ref_china  i.year#c.num_auths i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") append
** Column III: Add triple interaction with only one top50 author on paper
ppmlhdfe citation_count  c.dum2010##c.atleastone##c.one_top50 c.dum2010##c.desc_ref_china i.year#c.num_auths i.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id)
outreg2 using "`ofile'.tex", tex label dec(3) aster se bracket ctitle("Citation Count") addtext(Paper FEs, "Y", Author FEs, "N", Year FEs, "Y", Age of Paper FEs, "Y") append


************************************* Coefplot for effects by year in the double and triple interaction specifications*********************************

matrix summary=J(21,3,0)

************************************
** Figure A (I): Baseline eventstudy
reghdfe citation_count  ib2010.year##c.atleastone c.dum2010#c.desc_ref_china  ib2010.year i.paper_age if min_year>=2000 & year<=2020, absorb(panelid) vce(clus author_id_paper_id) allbaselevels
est store r_double1

preserve

forvalues j=1(1)21 {
	 local year = `j' + 1999
	 matrix summary[`j', 1]=_b[`year'.year#c.atleastone]
	 matrix summary[`j',2]=_b[`year'.year#c.atleastone]+1.645*_se[`year'.year#c.atleastone]
	 matrix summary[`j', 3]=_b[`year'.year#c.atleastone]-1.645*_se[`year'.year#c.atleastone]


	}
svmat summary
gen year_fig = _n + 1999 if _n < 22

twoway (connected summary1 year_fig, lwidth(thick) lcolor(gray) mcolor(black) msize(2)) ///
 (rcap summary2 summary3 year_fig, lcolor(black)), yline(0) ///
 title("A. Effects of Atleastone{subscript:j} x Year{subscript:t} (I)",size(5)) ///
 xlabel(2000 2002 2004 2006 2008 2010 2012 2014 2016 2018 2020, labsize(3) angle(45)) ///
 xtitle("Year") ytitle("Time-Varying Coefficients",size(4)) legend(off) graphregion(color(white)) ylabel(,labsize(3))
 graph export graph_double_effects1.png,replace
restore
************************************

************************************
** Figure A (II): Baseline + num auths x year
reghdfe citation_count  ib2010.year##c.atleastone ib2010.year##c.num_auths  c.dum2010#c.desc_ref_china  ib2010.year i.paper_age if min_year>=2000 & year<=2020 , absorb(panelid) vce(clus author_id_paper_id) allbaselevels
est store r_double2

preserve

forvalues j=1(1)21 {
	 local year = `j' + 1999
	 matrix summary[`j', 1]=_b[`year'.year#c.atleastone]
	 matrix summary[`j',2]=_b[`year'.year#c.atleastone]+1.645*_se[`year'.year#c.atleastone]
	 matrix summary[`j', 3]=_b[`year'.year#c.atleastone]-1.645*_se[`year'.year#c.atleastone]


	}
svmat summary
gen year_fig = _n + 1999 if _n < 22

twoway (connected summary1 year_fig, lwidth(thick) lcolor(gray) mcolor(black) msize(2)) ///
 (rcap summary2 summary3 year_fig, lcolor(black)), yline(0) ///
 title("A. Effects of Atleastone{subscript:j} x Year{subscript:t} (II)",size(5)) ///
 xlabel(2000 2002 2004 2006 2008 2010 2012 2014 2016 2018 2020, labsize(3) angle(45)) ///
 xtitle("Year") ytitle("Time-Varying Coefficients",size(4)) legend(off) graphregion(color(white)) ylabel(,labsize(3))
 graph export graph_double_effects2.png,replace
restore
************************************

************************************
** Figure B: Triple Interaction
reghdfe citation_count ib2010.year##c.atleastone##c.one_top50 ib2010.year##c.num_auths c.dum2010#c.desc_ref_china  ib2010.year i.paper_age if min_year>=2000 & year<=2020, absorb(panelid) vce(clus author_id_paper_id) allbaselevels
preserve 
	forvalues j=1(1)21 {
		local year = `j' + 1999
		matrix summary[`j',1]=_b[`year'.year#c.atleastone#c.one_top50]
		matrix summary[`j',2]=_b[`year'.year#c.atleastone#c.one_top50]+1.645*_se[`year'.year#c.atleastone#c.one_top50]
		matrix summary[`j',3]=_b[`year'.year#c.atleastone#c.one_top50]-1.645*_se[`year'.year#c.atleastone#c.one_top50]		
	}
svmat summary
gen year_fig = _n + 1999 if _n < 22

twoway (connected summary1 year_fig, lwidth(thick) lcolor(gray) mcolor(black) msize(2)) ///
 (rcap summary2 summary3 year_fig, lcolor(black)), yline(0) ///
 title("B. Effects of Atleastone{subscript:j} x One top50 Author{subscript:j}  x Year{subscript:t}",size(5)) ///
 xlabel(2000 2002 2004 2006 2008 2010 2012 2014 2016 2018 2020, labsize(3) angle(45)) ///
 xtitle("Year") ytitle("Time-Varying Coefficients",size(4)) legend(off) graphregion(color(white)) ylabel(,labsize(3))
graph export graph_triple_effects.png,replace	
restore
************************************