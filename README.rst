
Disclosure Extractor
====================

Disclsoure Extractor is an open source repository to extract data from PDFs
of judicial financial data
It was built for use with Courtlistener.com.

It uses image processing and OCRing to extract data on financial records.
Additional functionality estimates a judges' net worth from the disclosures.

Further development is intended and all contributors, corrections and additions are welcome.

Background
==========

Free Law Project built this to help extract out data from roughly 18k financial
records. These records are available for a limited period from the US Government
before they are destroyed.  In an effort to review roughly 20 years of records we needed
a method to extract out the information at a high degree of accuracy.

Quickstart
===========

Below is an example output from Justice Alitos' abbreviated output
from his 2011 disclosure, followed by the output in table format with
calculations.

The main function process_financial_document accepts a url, filepath,
or PDF as bytes.

::

    from disclosure_extractor import (
        process_financial_document,
        print_results
    )
    output = process_financial_document(filepath)


::

        returns:

        {
          "title": "Document title",
          "url": "Document download url if applicable",
          "type": "PDF",
          "page_count": 8,
          "sections": {
            "Positions": {
              "empty": true,
              "fields": [
                "Position",
                "Name of Organization"
              ],
              "rows": {}
            },
            "Agreements": {
              "empty": true,
              "fields": [
                "Date",
                "Parties and Terms"
              ],
              "rows": {}
            },
            "Non-Investment Income": {
              "empty": false,
              "fields": [
                "Date",
                "Source and Type",
                "Income"
              ],
              "rows": {
                "0": {
                  "Date": {
                    "text": "1. 85/2011",
                    "is_redacted": false
                  },
                  "Source and Type": {
                    "text": "Duquesne University School of Law - Teaching",
                    "is_redacted": false
                  },
                  "Income": {
                    "text": "$15,000.00",
                    "is_redacted": false
                  }
                }
              }
            },
            "Non Investment Income Spouse": {
              "empty": true,
              "fields": [
                "Date",
                "Source and Type"
              ],
              "rows": {}
            },
            "Reimbursements": {
              "empty": false,
              "fields": [
                "Source",
                "Dates",
                "Locations",
                "Purpose",
                "Items Paid or Provided"
              ],
              "rows": {
                "0": {
                  "Source": {
                    "text": "1. University of Hawaii",
                    "is_redacted": false
                  },
                  "Dates": {
                    "text": "January 22-30, 2011",
                    "is_redacted": false
                  },
                  "Locations": {
                    "text": "Honolulu, Hawaii",
                    "is_redacted": false
                  },
                  "Purpose": {
                    "text": "Teaching",
                    "is_redacted": false
                  },
                  "Items Paid or Provided": {
                    "text": "Transportution, Meals, Lodging.",
                    "is_redacted": false
                  }
                }
              }
            },
            "Gifts": {
              "empty": true,
              "fields": [
                "Source",
                "Description",
                "Value"
              ],
              "rows": {}
            },
            "Liabilities": {
              "empty": true,
              "fields": [
                "Creditor",
                "Description",
                "Value Code"
              ],
              "rows": {}
            },
            "Investments and Trusts": {
              "empty": false,
              "help": {
                "A": "Description of Assets",
                "B1": "Amount Code (A-H)",
                "B2": "Type",
                "C1": "Value Code 2",
                "C2": "Value Method Code 3",
                "D1": "Type",
                "D2": "Date Month/Day",
                "D3": "Value Code 2",
                "D4": "Gain Code 1",
                "D5": "Identity of Buyer/Seller (if private)"
              },
              "fields": [
                "A",
                "B1",
                "B2",
                "C1",
                "C2",
                "D1",
                "D2",
                "D3",
                "D4",
                "D5"
              ],
              "rows": {
                "0": {
                  "A": {
                    "text": "US Savings Bonds Series EE (Y)",
                    "is_redacted": false
                  },
                  "B1": {
                    "text": "",
                    "is_redacted": false
                  },
                  "B2": {
                    "text": "",
                    "is_redacted": false
                  },
                  "C1": {
                    "text": "",
                    "is_redacted": false
                  },
                  "C2": {
                    "text": "",
                    "is_redacted": false
                  },
                  "D1": {
                    "text": "",
                    "is_redacted": false
                  },
                  "D2": {
                    "text": "",
                    "is_redacted": false
                  },
                  "D3": {
                    "text": "",
                    "is_redacted": false
                  },
                  "D4": {
                    "text": "",
                    "is_redacted": false
                  },
                  "D5": {
                    "text": "",
                    "is_redacted": false
                  }
                }
              }
            }
          },
          "Additional Information or Explanations": {
            "is_redacted": false,
            "text": "Part Vil: 19, My interest in the Duke Retirement Plan (Vanguard Target Retirement Account 2015) is derived in its entirety from an employer contribution, which is not listed as outside earned income on the ground that it is not taxable Information on assets held by children who are no longer dependents is omitted. May 10, 2011 - A charitable contribution of $2,000 was made on my behalf by the Manhattan Institute for which I gave a speech in October 2010."
          },
          "pdf_size": 564580,
          "date_created": null,
          "success": true,
          "msg": null,
          "nomination": false,
          "amended": false,
          "initial": false,
          "annual": true,
          "final": false,
          "reporting_period": "6, Reporting Period OVOL2011 wo 12/31/2011",
          "date_of_report": "8/13/2012",
          "court": "United States Supreme Court",
          "judge": "Alito, Samuel A.",
          "wealth": {
            "investment_net_worth": [
              380018,
              1130000
            ],
            "income_gains": [
              7515,
              26500
            ],
            "liabilities": [
              0,
              0
            ],
            "salary_income": 26955.0
          }
        }





Printing Results
===========================
Below is an illustrative example from Justice Alito

::

    | --------------------------------------------------------------------------- |
    | Non-Investment Income                                                       |
    | --------------------------------------------------------------------------- |
    | Date          | Source and Type                               | Income      |
    | --------------------------------------------------------------------------- |
    | 1. 8/5/2011   | Duquesne University School of Law - Teaching  | $15,000.00  |
    | 2. 8/25/2011  | Duke Law School - Teaching                    | $11,955.00  |
    | ___________________________________________________________________________ |


    | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | Reimbursements                                                                                                                                             |
    | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | Source                                        | Dates                  | Locations               | Purpose              | Items Paid or Provided           |
    | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | 1. University of Hawaii                       | January 22-30, 2011    | Honolulu, Hawaii        | Teaching             | Transportution, Meals, Lodging.  |
    | 2. The Federalist Society                     | March 10-14, 2011      | Menlo Park, California  | Speaking Engagement  | Transportation, Meals, Lodging   |
    | 3. Bar Association of Metropolitan St. Louis  | May 15-17, 2011        | St. Louis, Missouri     | Speaking Engagement  | Transportation, Meals, Lodging   |
    | 4. Duquesne University School of Law          | July 5-15, 2011        | Rome, Italy             | Teaching             | Transportation, Meals, Lodging   |
    | 5. Duke Law School                            | September 12-16, 2011  | Durham, North Carolina  | Teaching             | Transportation, Meals, Lodging   |
    | 7. Rutgers University School of Law           | November 15, 2011      | Newark, New Jersey      | Speaking Engagement  | Transportation, Meal             |
    | __________________________________________________________________________________________________________________________________________________________ |


    | ------------------------------------------------------------------------------------------------------------- |
    | Investments and Trusts                                                                                        |
    | ------------------------------------------------------------------------------------------------------------- |
    | A                                       | B1 | B2        | C1 | C2 | D1     | D2        | D3 | D4 | D5        |
    | ------------------------------------------------------------------------------------------------------------- |
    | US Savings Bonds Series EE (Y)          |    |           |    |    |        |           |    |    |           |
    | Vang. Tax Ex. Mny, Mkt, Fund            | A  | Interest  | J  | T  |        |           |    |    |           |
    | Vang. Inter. Term Tax Ex. Fund          | A  | Interest  | J  | T  |        |           |    |    |           |
    | Vang. L. T. Tax Ex. Fund                | A  | Interest  | J  | T  |        |           |    |    |           |
    | Vang. Star Mut. Fund                    | A  | Dividend  | K  | T  |        |           |    |    |           |
    | Vang. Wellington Mut. Fund              | C  | Dividend  | M  | T  |        |           |    |    |           |
    | Smith Bamey Money Funds Cash Port.      | A  | Dividend  | J  | T  |        |           |    |    |           |
    | PNC Bank Account                        | A  | Interest  | K  | T  |        |           |    |    |           |
    | Vang. Small Cap, Stock Fund             | B  | Dividend  | L  | T  |        |           |    |    |           |
    | Vang. Total Stock Mkt. Index P.         | B  | Dividend  | M  | T  |        |           |    |    |           |
    | Windsor II                              | A  | Dividend  | J  | T  | part)  | 06/14/11  | J  | B  |           |
    | Fidelity Eq.-Ine. I Pund (Y)            |    |           |    |    |        |           |    |    |           |
    | Vang. Tax Ex. Mny Mkt.                  | A  | Interest  | J  | T  |        |           |    |    |           |
    | Citibank Deposit Program                | A  | Interest  | J  | T  |        |           |    |    |           |
    | BMY Common Stock (Y)                    |    |           |    |    |        |           |    |    |           |
    | XOM Common Stock                        | B  | Dividend  | M  | T  |        |           |    |    |           |
    | PNC Bank Account                        |    | None      | J  | T  |        |           |    |    |           |
    | Edward Jones Investment (cash account)  |    | None      | J  | T  |        |           |    |    |           |
    | Vanguard Target Retirement Acct. 2015   | B  | Int/Div.  | J  | T  | Open   | 8/24/11   | J  |    | Part VII  |
    | _____________________________________________________________________________________________________________ |


    Wealth
    =======
    Investments Total:        $380,018 to $1,130,000
    Investments gains YOY:    $7,515 to $26,500
    Percent gains YOY:        2.02%
    Debts:                    $0 to $0
    Other incomes totaling:   $26,955.00



Fields
======

The main sections are as follows.

1. :code:`Positions` ==> dict;
2. :code:`Agreements` ==> dict;
3. :code:`Non-Investment Income` ==> dict;
4. :code:`Non Investment Income Spouse` ==> dict;
5. :code:`Reimbursements` ==> dict;
6. :code:`Gifts` ==> dict;
7. :code:`Liabilities` ==> dict;
8. :code:`Investments and Trusts` ==> dict;
9. :code:`Additional Information or Explanations` ==> dict;


Installation
============

Installing disclosure-extractor will be easy.


        pip install disclosure-extractor


Or install the latest dev version from github


        pip install git+https://github.com/freelawproject/disclosure-extractor.git@master



Future
=======

1) Continue to improve output for older financial disclosures

Deployment
==========

Releasing a new version to PyPI is handled in a Github workflow.

Once a version is ready to be released, adjust the version number in the
setup.py file and add tag the branch in the following format and push to github.

::

    v*.*.*

The action will build and push to PyPI.



If you wish to create a new version manually, the process is:

1. Update version info in ``setup.py``

2. Install the requirements in requirements_dev.txt

3. Set up a config file at ~/.pypirc

4. Generate a universal distribution that worksin py2 and py3 (see setup.cfg)

    ::

        python setup.py sdist bdist_wheel

5. Upload the distributions

    ::

        twine upload dist/* -r pypi (or pypitest)

        python setup.py sdist upload -r pypi

License
=======

This repository is available under the permissive BSD license, making it easy and safe to incorporate in your own libraries.

Pull and feature requests welcome. Online editing in Github is possible (and easy!)
