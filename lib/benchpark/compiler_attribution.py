# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment_helper import ExperimentHelper


class CompilerAttribution:
    features = (
        "association",
        "remark_counts",
        "remark_details",
        "kru",
        "ir_metrics",
        "per_pass_ir_metrics",
    )

    variant(
        "compiler_attribution",
        default="none",
        values=("none",) + features,
        multi=True,
        description="Compiler attribution features to enable",
    )

    class Helper(ExperimentHelper):
        def selected_features(self):
            return [
                feature
                for feature in CompilerAttribution.features
                if self.spec.satisfies(f"compiler_attribution={feature}")
            ]

        def compute_modifiers_section(self):
            return [
                {"name": "compiler_attribution", "mode": feature}
                for feature in self.selected_features()
            ]

        def compute_package_section(self):
            features = self.selected_features()
            if not features:
                return {}

            feature_specs = " ".join(f"+{feature}" for feature in features)
            return {
                "packages": {
                    "compiler_attribution_plugin": {
                        "spack_pkg_spec": (
                            f"compiler-attribution-plugin {feature_specs}"
                        )
                    }
                }
            }
