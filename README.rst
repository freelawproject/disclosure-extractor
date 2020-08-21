# Disclosure Extractor
This program extracts federal judicial financial disclosures.

Disclosure Extractor
=========

Disclsoure Extractor is an open source repository to extract data from PDFs 
of judicial financial data
It was built for use with Courtlistener.com.

It uses image processing and OCRing to extract data on financial records.
Additonal functionality estimates a Judge networth from the disclosures. 

Further development is intended and all contributors, corrections and additions are welcome.

Background
==========

Free Law Project built this to help extract out data from roughly 18k financial 
records. These records are available for a limited period from the US Government
before they are destroyed.  In an effort to review roughly 20 years of records we needed 
a method to extract out the information at a high degree of accuracy.

Quickstart
===========

Below is an example output but will need to be updated further

::

        IMPORTS


        returns:
          [
            {
            "positions": [
                {
                "position": "Trustee",
                "name_of_organization": "Sesame Street"
                }
            ]
            "agreements": [
                {
                  "date": "",
                  "parties_and_terms": ""
                },
            ]
            "judge_income": [
                {
                  "date": "1. 1/1/2020",
                  "source_type": "",
                  "income": ""
                },
            ]
            "spouse_income": [
                {
                  "date": "1.2011",
                  "source_type": "Commonwealth of Massachusetts - salary"
                },
            ]
            "reimbursements": [
                {
                  "source": "1. University of Rochester",
                  "dates": "April 20, 2011",
                  "location": "Rochester, NY",
                  "purpose": "Guest Teacher",
                  "item_paid_or_provided": "Transportation"
                },
            ]
            "gifts": [
                {
                  "source": "",
                  "description": "",
                  "value": ""
                },
            ]
            "liabilities": [
                {
                  "creditor": "1. Cambridge Bank N.A., now known as: TD Bank N.A,",
                  "description": "Partial guarantee of commercial loan to Carrollton, LLC (Part VII, Line 190)",
                  "value_code": "P1"
                },
                {
                  "creditor": "2. Cambridge Trust Bank",
                  "description": "Partial guarantee of commercial loan to XYZ, LLC (Part VII, Line 190)",
                  "value_code": "P1"
                },
            ]
            "investments_and_trusts": [
                {
                  "description_of_asset": ". Cambridge Trust Account",
                  "amount_code": "A",
                  "income_type": "Interest",
                  "gross_value": "K",
                  "gross_value_code": "T",
                  "transactions_type": "",
                  "transaction_date": "",
                  "transaction_value_code": "",
                  "transaction_gain_value_code": "",
                  "id_buyer_or_seller": ""
                }
            ]





Some Notes ...
======================

There are multiple methods for extracting data, including
multiple image processing methods.


Fields
======

A work in progress still.

High level field data include.
1. :code:`positions` =`=> array; 
2. :code:`agreements` ==> array; 
3. :code:`judge_income` ==>  array;
3. :code:`spouse_income` ==>  array;
3. :code:`reimbursements` ==>  array;
3. :code:`judge_income` ==>  array;
3. :code:`gifts` ==>  array;
3. :code:`liabilities` ==>  array;
3. :code:`investments`_and_trusts` ==>  array;


Installation
============

Installing disclosure-extractor will be easy.

    
        pip install disclosure-extractor


Or install the latest dev version from github

    
        pip install git+https://github.com/freelawproject/disclosure-extractor.git@master



Future
=======

1) Continue to improve ...
2) Future updates

Deployment
==========

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



License
=======

This repository is available under the permissive BSD license, making it easy and safe to incorporate in your own libraries.

Pull and feature requests welcome. Online editing in Github is possible (and easy!)
