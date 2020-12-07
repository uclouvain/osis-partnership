from datetime import date

from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from partnership.utils import (
    academic_dates,
    academic_years,
    merge_agreement_ranges,
    get_attribute,
)


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


class UtilAcademicDisplayTest(TestCase):
    def test_academic_dates(self):
        start = date(2020, 7, 2)
        end = date(2020, 9, 30)
        self.assertEqual(academic_dates('', ''), "N/A")
        self.assertEqual(academic_dates(None, None), "N/A")
        self.assertEqual(academic_dates(start, None), "02/07/2020 > N/A")
        self.assertEqual(academic_dates('', end), "N/A > 30/09/2020")
        self.assertEqual(academic_dates(start, end), "02/07/2020 > 30/09/2020")

    def test_academic_years(self):
        start = AcademicYearFactory(year=2150)
        end = AcademicYearFactory(year=2151)
        self.assertEqual(academic_years('', ''), "N/A")
        self.assertEqual(academic_years(None, None), "N/A")
        self.assertEqual(academic_years(start, None), "2150-51 > N/A")
        self.assertEqual(academic_years('', end), "N/A > 2151-52")
        self.assertEqual(academic_years(start, end), "2150-51 > 2151-52")


class UtilGetNestedAttributeTest(TestCase):
    def test_get_attribute(self):
        obj = type('test', (object,), {})()
        self.assertEqual(get_attribute(obj, 'foo.bar'), '')
        obj.foo = {'bar': 42}
        self.assertEqual(get_attribute(obj, 'foo'), "{'bar': 42}")
        self.assertEqual(get_attribute(obj, 'foo.bar'), '42')
        self.assertEqual(get_attribute(obj, 'foo.bar', cast_str=False), 42)
        self.assertEqual(get_attribute(obj, 'foo.baz', default=0), 0)
