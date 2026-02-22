"""
Tests for the naming convention parser.

Run with: pytest tests/test_parser.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import parse_ad_name, detect_schema


class TestDetectSchema:
    def test_schema_1_sources(self):
        assert detect_schema("CFC") == 1
        assert detect_schema("Katrin") == 1
        assert detect_schema("Claudio") == 1
        assert detect_schema("Katrin+Claudio") == 1
        assert detect_schema("CFK") == 1
        assert detect_schema("CFS") == 1
        assert detect_schema("IN") == 1

    def test_schema_2_sources(self):
        assert detect_schema("MT") == 2
        assert detect_schema("SM") == 2
        assert detect_schema("CreativeTeam") == 2
        assert detect_schema("DCO") == 2
        assert detect_schema("addictive") == 2
        assert detect_schema("stronger") == 2

    def test_schema_3_fallback(self):
        assert detect_schema("Unknown") == 3
        assert detect_schema("") == 3
        assert detect_schema("SomeNewAgency") == 3


class TestCoreFields:
    def test_basic_7_fields(self):
        ad = "Socken_C042_Video_UGC_Testimonial_In_CFC"
        result = parse_ad_name(ad)

        assert result["product"] == "Socken"
        assert result["creative_id"] == "C042"
        assert result["content_type"] == "Video"
        assert result["adtype"] == "UGC"
        assert result["creative_cluster"] == "Testimonial"
        assert result["in_ex"] == "In"
        assert result["creative_source"] == "CFC"
        assert result["schema_version"] == 1

    def test_schema_2_core(self):
        ad = "Boxershorts_C100_Image_Statics_Product_Ex_MT"
        result = parse_ad_name(ad)

        assert result["product"] == "Boxershorts"
        assert result["content_type"] == "Image"
        assert result["creative_source"] == "MT"
        assert result["schema_version"] == 2

    def test_schema_3_core(self):
        ad = "Retro_C200_Video_Motion_Lifestyle_In_NewAgency"
        result = parse_ad_name(ad)

        assert result["product"] == "Retro"
        assert result["creative_source"] == "NewAgency"
        assert result["schema_version"] == 3

    def test_empty_ad_name(self):
        result = parse_ad_name("")
        assert result["parse_errors"]
        assert result["product"] is None

    def test_too_few_segments(self):
        result = parse_ad_name("Socken_C042_Video")
        assert result["parse_errors"]
        assert result["product"] == "Socken"
        assert result["creative_id"] == "C042"
        assert result["content_type"] == "Video"
        assert result["adtype"] is None


class TestSchema1:
    def test_with_optional_fields(self):
        ad = "Socken_C042_Video_UGC_Testimonial_In_CFC_PL-SOC_Blau_EL1_CR01_SummerSale_916_H1_T1_V1_A1_M_T01_2503"
        result = parse_ad_name(ad)

        assert result["schema_version"] == 1
        assert result["pl_eg_sp"] == "PL-SOC"
        assert result["color"] == "Blau"
        assert result["element"] == "EL1"
        assert result["cr_kuerzel"] == "CR01"
        assert result["creative_tag"] == "SummerSale"
        assert result["format_video"] == "916"
        assert result["hook"] == "H1"
        assert result["text_kuerzel"] == "T1"
        assert result["visual"] == "V1"

    def test_image_no_hook(self):
        """Images should get format_foto but not hook/text/visual."""
        ad = "Socken_C042_Image_Statics_Product_In_CFC_PL-SOC_Blau_EL1_CR01_SummerSale_11"
        result = parse_ad_name(ad)

        assert result["format_foto"] == "11"
        assert result["format_video"] is None
        assert result["hook"] is None

    def test_ai_flag(self):
        ad = "Socken_C042_Video_UGC_Testimonial_In_CFC_PL-SOC_Blau_EL1_CR01_Tag_916_H1_T1_V1_A1_M_T01_2503_C001_Info_Free_AI"
        result = parse_ad_name(ad)

        assert result["is_ai"] is True

    def test_raw_suffix_preserved(self):
        ad = "Socken_C042_Video_UGC_Testimonial_In_CFC_some_extra_fields"
        result = parse_ad_name(ad)

        assert result["raw_suffix"] is not None
        assert "some" in result["raw_suffix"]


class TestSchema2:
    def test_with_optional_fields(self):
        ad = "Socken_C100_Image_Statics_Product_Ex_MT_PL-SOC-Rot_T01_VC1_CC1_F_TE1_TA1_IT1_CP1_EL1_2503"
        result = parse_ad_name(ad)

        assert result["schema_version"] == 2
        assert result["pl_eg_sp"] == "PL-SOC"
        assert result["color"] == "Rot"
        assert result["test_ids"] == "T01"
        assert result["visual_ct"] == "VC1"
        assert result["creator_cluster"] == "CC1"
        assert result["gender"] == "F"

    def test_pl_color_hyphen_parsing(self):
        ad = "Socken_C100_Image_Statics_Product_Ex_SM_PL-SOC-DunkelBlau"
        result = parse_ad_name(ad)

        assert result["pl_eg_sp"] == "PL-SOC"
        assert result["color"] == "DunkelBlau"


class TestSchema3:
    def test_minimal(self):
        ad = "Retro_C200_Video_Motion_Lifestyle_In_NewAgency_EG_T01"
        result = parse_ad_name(ad)

        assert result["schema_version"] == 3
        assert result["pl_eg_sp"] == "EG"
        assert result["test_ids"] == "T01"

    def test_only_core(self):
        ad = "Retro_C200_Video_Motion_Lifestyle_In_NewAgency"
        result = parse_ad_name(ad)

        assert result["schema_version"] == 3
        assert result["pl_eg_sp"] is None
        assert result["test_ids"] is None
