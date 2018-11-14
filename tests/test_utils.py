from datetime import date

from django.test import TestCase

from partnership.utils import merge_agreement_ranges


class MergeAgreementRangesTest(TestCase):
    def test_single_range(self):
        ranges = [
            {'start': 2010, 'end': 2012},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, [{'start': 2010, 'end': 2012}])

    def test_several_included_ranges(self):
        ranges = [
            {'start': 2010, 'end': 2012},
            {'start': 2012, 'end': 2015},
            {'start': 2014, 'end': 2016},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, [{'start': 2010, 'end': 2016}])

    def test_several_separated_ranges(self):
        ranges = [
            {'start': 2010, 'end': 2012},
            {'start': 2014, 'end': 2015},
            {'start': 2017, 'end': 2018},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, ranges)

    def test_mixed_ranges(self):
        ranges = [
            {'start': 2010, 'end': 2012},
            {'start': 2014, 'end': 2017},
            {'start': 2016, 'end': 2018},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, [
            {'start': 2010, 'end': 2012},
            {'start': 2014, 'end': 2018},
        ])

    def test_range_in_range(self):
        ranges = [
            {'start': 2010, 'end': 2020},
            {'start': 2013, 'end': 2017},
            {'start': 2016, 'end': 2018},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, [
            {'start': 2010, 'end': 2020},
        ])

    def test_several_same_ranges(self):
        ranges = [
            {'start': 2010, 'end': 2013},
            {'start': 2010, 'end': 2013},
            {'start': 2015, 'end': 2016},
            {'start': 2015, 'end': 2017},
        ]
        merged_ranges = merge_agreement_ranges(ranges)
        self.assertListEqual(merged_ranges, [
            {'start': 2010, 'end': 2013},
            {'start': 2015, 'end': 2017},
        ])
