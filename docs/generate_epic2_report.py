"""Generate Epic 2 Course-Style Documentation PDF — ML Ensemble + SHAP.

Run:  python docs/generate_epic2_report.py

Produces: docs/Epic2_ML_Ensemble_SHAP.pdf
"""

from __future__ import annotations

from fpdf import FPDF


class CoursePDF(FPDF):
    """Custom PDF with header/footer and styling helpers."""

    PRIMARY = (41, 98, 255)
    DARK = (30, 30, 30)
    GRAY = (100, 100, 100)
    LIGHT_BG = (245, 247, 250)
    WHITE = (255, 255, 255)
    GREEN = (34, 197, 94)
    AMBER = (245, 158, 11)
    RED = (239, 68, 68)
    ACCENT = (99, 102, 241)
    TIP_BG = (219, 234, 254)
    TIP_BORDER = (59, 130, 246)
    WARN_BG = (254, 243, 199)
    WARN_BORDER = (245, 158, 11)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.GRAY)
        self.cell(0, 8, "EmoraTest - Epic 2: ML Ensemble + SHAP", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, "EmoraTest AI Platform - Course Documentation", align="C")

    # ── Styling helpers ──────────────────────────────────────

    def chapter_title(self, num: str, title: str):
        self.add_page()
        self.ln(10)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*self.PRIMARY)
        self.cell(0, 12, f"Chapter {num}", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*self.DARK)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y() + 2, self.l_margin + 80, self.get_y() + 2)
        self.ln(8)

    def section_title(self, num: str, title: str):
        self.ln(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.PRIMARY)
        self.cell(0, 9, f"{num}  {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.l_margin + 50, self.get_y())
        self.ln(3)

    def subsection(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.DARK)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.cell(indent, 5.5, "")
        w = self.w - self.l_margin - self.r_margin - indent - 5
        self.cell(5, 5.5, "- ")
        self.multi_cell(w, 5.5, text)

    def numbered(self, num: int, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "B", 10)
        self.cell(8, 5.5, f"{num}.")
        self.set_font("Helvetica", "", 10)
        w = self.w - self.l_margin - self.r_margin - indent - 13
        self.multi_cell(w, 5.5, text)

    def code_block(self, text: str):
        self.set_fill_color(*self.LIGHT_BG)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(60, 60, 60)
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        lines = text.strip().split("\n")
        h = len(lines) * 4.5 + 6
        if self.get_y() + h > self.h - 25:
            self.add_page()
        self.rect(x, self.get_y(), w, h, style="F")
        self.set_xy(x + 4, self.get_y() + 3)
        for line in lines:
            self.cell(0, 4.5, line[:95], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 4)
        self.ln(4)

    def tip_box(self, title: str, text: str):
        self._callout(title, text, self.TIP_BG, self.TIP_BORDER)

    def warn_box(self, title: str, text: str):
        self._callout(title, text, self.WARN_BG, self.WARN_BORDER)

    def _callout(self, title: str, text: str, bg: tuple, border_color: tuple):
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        self.set_fill_color(*bg)
        self.set_draw_color(*border_color)
        y_start = self.get_y()
        # Estimate height
        self.set_font("Helvetica", "", 9)
        lines = len(text) / (w / 2) + 3
        h = max(lines * 5, 14)
        if y_start + h > self.h - 25:
            self.add_page()
            y_start = self.get_y()
        self.rect(x, y_start, w, h, style="FD")
        self.set_line_width(1.2)
        self.line(x, y_start, x, y_start + h)
        self.set_line_width(0.3)
        self.set_xy(x + 4, y_start + 2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*border_color)
        self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        self.set_x(x + 4)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK)
        self.multi_cell(w - 8, 4.5, text)
        self.set_y(y_start + h + 3)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            available = self.w - self.l_margin - self.r_margin
            col_widths = [available / len(headers)] * len(headers)
        self.set_fill_color(*self.PRIMARY)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 8)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        alt = False
        for row in rows:
            if alt:
                self.set_fill_color(240, 242, 245)
            else:
                self.set_fill_color(*self.WHITE)
            self.set_text_color(*self.DARK)
            for i, cell in enumerate(row):
                a = "L" if i == 0 else "C"
                self.cell(col_widths[i], 6, cell[:40], border=1, fill=True, align=a)
            self.ln()
            alt = not alt
        self.ln(3)


def build_pdf():
    pdf = CoursePDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    # ══════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*CoursePDF.PRIMARY)
    pdf.cell(0, 15, "EmoraTest", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*CoursePDF.GRAY)
    pdf.cell(0, 8, "AI Behavioral Intelligence for E-Commerce", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(15)
    pdf.set_draw_color(*CoursePDF.PRIMARY)
    pdf.set_line_width(0.8)
    mid = pdf.w / 2
    pdf.line(mid - 40, pdf.get_y(), mid + 40, pdf.get_y())
    pdf.ln(15)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*CoursePDF.DARK)
    pdf.cell(0, 12, "Epic 2: ML Ensemble + SHAP", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "CONV-22 to CONV-27  |  Sprint 2", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*CoursePDF.GRAY)
    pdf.cell(0, 8, "A course-style guide to ensemble ML, explainability,", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "and psychology-driven intervention systems", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(30)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*CoursePDF.GRAY)
    pdf.cell(0, 6, "Date: March 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Version: 1.0", align="C", new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*CoursePDF.DARK)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    toc = [
        ("1", "Prerequisites & What You'll Learn"),
        ("2", "Ensemble Models: Combining Multiple Classifiers"),
        ("3", "SHAP Explainability: Why Did the Model Decide That?"),
        ("4", "Psychology-Aware Interventions: From ML to Action"),
        ("5", "Real-Time Scoring Service: Putting It All Together"),
        ("6", "Model Evaluation & A/B Testing"),
        ("7", "Integration Testing: Validating the Pipeline"),
        ("8", "Architecture & Data Flow Diagrams"),
        ("9", "Exercises & Challenges"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*CoursePDF.PRIMARY)
        pdf.cell(10, 7, f"{num}.")
        pdf.set_text_color(*CoursePDF.DARK)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════════════════════════
    # CHAPTER 1: Prerequisites
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("1", "Prerequisites & What You'll Learn")

    pdf.section_title("1.1", "What Epic 1 Built (Recap)")
    pdf.body(
        "Before diving into Epic 2, let's recap what was built in Epic 1 "
        "(Data Foundation & ML Baseline). Understanding this foundation is "
        "essential because every component in Epic 2 builds directly on it."
    )
    pdf.subsection("The Three Models")
    pdf.body(
        "Epic 1 trained three independent XGBoost classifiers, each solving "
        "a different prediction problem using the same 8 behavioral features "
        "extracted from user browsing sessions:"
    )
    pdf.numbered(1, "Conversion Predictor (predictor_v1.pkl) - Binary classifier: "
                 "will this user purchase or abandon? Trained with SMOTE oversampling "
                 "to handle the 4% conversion rate imbalance. Target AUC >= 0.70.")
    pdf.numbered(2, "Intent Classifier (intent_v1.pkl) - 4-class classifier: "
                 "is the user browsing, comparing, deciding, or exiting? Uses "
                 "multi:softmax objective with LabelEncoder for class mapping.")
    pdf.numbered(3, "Friction Detector (friction_v1.pkl) - Binary classifier: "
                 "is this session experiencing high or low friction? Uses "
                 "scale_pos_weight for imbalance. Already had a SHAP TreeExplainer.")

    pdf.subsection("The 8 Behavioral Features")
    pdf.table(
        ["Feature", "Type", "What It Measures"],
        [
            ["hesitation_score", "0-1", "Pauses before clicks (decision paralysis)"],
            ["price_dwell_time_s", "seconds", "Time on price elements (price sensitivity)"],
            ["rage_click_score", "0-1", "Rapid repeated clicks (frustration)"],
            ["scroll_retreat_count", "int", "Scroll direction reversals (indecision)"],
            ["exit_intent_count", "int", "Attempts to leave (abandonment signal)"],
            ["checkout_hesitation_s", "seconds", "Idle time at checkout (commitment fear)"],
            ["velocity_variance", "float", "Mouse speed variance (erratic behavior)"],
            ["session_duration_s", "seconds", "Total session length"],
        ],
        [55, 25, 110],
    )

    pdf.subsection("The Psychology Framework")
    pdf.body(
        "Epic 1 also defined 8 psychological states in framework_v1.json, "
        "each mapping behavioral feature thresholds to evidence-based "
        "interventions. For example, 'Loss Aversion' triggers when "
        "checkout_hesitation >= 15s AND price_dwell >= 10s."
    )

    pdf.section_title("1.2", "What You'll Learn in This Guide")
    pdf.body("By the end of this guide, you will understand:")
    pdf.numbered(1, "How to combine multiple ML models into an ensemble that is "
                 "more reliable than any single model alone")
    pdf.numbered(2, "How SHAP (SHapley Additive exPlanations) works and why it's "
                 "the gold standard for ML explainability")
    pdf.numbered(3, "How to bridge the gap between ML predictions and actionable "
                 "business interventions using psychology")
    pdf.numbered(4, "How to build a real-time scoring service that orchestrates "
                 "models, explanations, and recommendations")
    pdf.numbered(5, "How to statistically compare models and analyze A/B tests")
    pdf.numbered(6, "How to write integration tests that validate cross-component contracts")

    # ══════════════════════════════════════════════════════════
    # CHAPTER 2: Ensemble Models
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("2", "Ensemble Models: Combining Multiple Classifiers")

    pdf.section_title("2.1", "Why Not Just Use One Model?")
    pdf.body(
        "Imagine you're a doctor diagnosing a patient. Would you rely on a "
        "single test, or would you combine blood work, imaging, and symptoms? "
        "The same principle applies to ML. Each of our three models sees the "
        "user session from a different angle:"
    )
    pdf.bullet("The conversion predictor asks: 'Will they buy?'")
    pdf.bullet("The intent classifier asks: 'What are they trying to do?'")
    pdf.bullet("The friction detector asks: 'Are they struggling?'")
    pdf.ln(2)
    pdf.body(
        "A user might have high conversion probability (they've added items "
        "to cart) but also high friction (they're rage-clicking the checkout "
        "button). No single model captures this full picture. An ensemble does."
    )

    pdf.section_title("2.2", "Our Ensemble Approach: Weighted Combination")
    pdf.body(
        "There are two common approaches to ensembles: (1) train a meta-model "
        "that learns to combine base model outputs (stacking), or (2) use a "
        "transparent weighted average. We chose option 2 because:"
    )
    pdf.bullet("Interpretability: we can explain exactly why a score is what it is")
    pdf.bullet("No additional training data: stacking requires held-out predictions")
    pdf.bullet("Simplicity: fewer moving parts means fewer failure modes")
    pdf.ln(2)

    pdf.subsection("The Session Score Formula")
    pdf.body(
        "The ensemble produces a single 'session_score' between 0 and 1, "
        "representing overall abandonment risk. The formula is:"
    )
    pdf.code_block(
        "session_score = (\n"
        "    0.5 * (1 - conversion_prob)   # Higher conversion = lower risk\n"
        "    + 0.3 * friction_prob          # Higher friction = higher risk\n"
        "    + 0.2 * intent_risk            # 'exiting' = 0.9 risk, 'browsing' = 0.3\n"
        ")"
    )

    pdf.tip_box(
        "Key Insight: Inverting the Conversion Signal",
        "Notice we use (1 - conversion_prob). This is because the conversion model "
        "predicts likelihood of PURCHASE, but our ensemble measures RISK. High "
        "purchase probability = low risk. This inversion is easy to forget and "
        "causes subtle bugs if you get the direction wrong."
    )

    pdf.subsection("Why These Weights?")
    pdf.body(
        "The default weights (0.5, 0.3, 0.2) reflect business priority: "
        "conversion prediction is the most direct signal, friction adds "
        "diagnostic value, and intent provides behavioral context. These "
        "weights are configurable via EnsembleConfig, making it easy to "
        "tune them per merchant or run ablation studies."
    )

    pdf.section_title("2.3", "The Action Ladder")
    pdf.body(
        "The session score maps to one of four actions, creating a graduated "
        "response system. This prevents over-intervention (annoying low-risk "
        "users) while ensuring high-risk sessions get immediate attention:"
    )
    pdf.table(
        ["Score Range", "Action", "What Happens"],
        [
            ["< 0.30", "monitor", "No intervention. User is fine."],
            ["0.30 - 0.49", "nudge", "Soft engagement (subtle trust signals)"],
            ["0.50 - 0.74", "intervene", "Active intervention (targeted help)"],
            [">= 0.75", "urgent", "Last-chance retention (exit discount)"],
        ],
        [35, 30, 125],
    )

    pdf.section_title("2.4", "Confidence: How Sure Are We?")
    pdf.body(
        "Besides the score, the ensemble computes a 'confidence' metric that "
        "measures how much the three models agree. If all three models point "
        "in the same direction (all say risky OR all say safe), confidence is "
        "high. If they disagree (conversion says safe but friction says "
        "dangerous), confidence drops."
    )
    pdf.body(
        "This is critical for the business: a high-risk score with low "
        "confidence might mean 'wait and gather more data' rather than "
        "'intervene immediately'. Confidence is computed from:"
    )
    pdf.bullet("Each model's certainty (distance from the 0.5 decision boundary)")
    pdf.bullet("Agreement between conversion and friction risk signals")
    pdf.bullet("How peaked the intent probability distribution is")

    pdf.section_title("2.5", "Implementation (CONV-22)")
    pdf.body("File: ml/src/ensemble/ensemble.py")
    pdf.code_block(
        "from src.ensemble.ensemble import EnsembleModel\n\n"
        "ensemble = EnsembleModel()  # default weights\n"
        "result = ensemble.score(\n"
        "    conversion_prob=0.8,\n"
        "    intent_label='browsing',\n"
        "    intent_probs={'browsing': 0.7, 'comparing': 0.2, ...},\n"
        "    friction_prob=0.2,\n"
        ")\n"
        "print(result.session_score)       # 0.22 (low risk)\n"
        "print(result.recommended_action)  # 'monitor'\n"
        "print(result.confidence)          # 0.85 (high agreement)"
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 3: SHAP Explainability
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("3", "SHAP: Why Did the Model Decide That?")

    pdf.section_title("3.1", "The Explainability Problem")
    pdf.body(
        "XGBoost models are powerful but opaque. When the friction detector says "
        "'this session has 87% friction probability', a merchant rightfully asks: "
        "'Why? What specifically is causing friction?' Without an answer, the "
        "prediction is useless for action."
    )
    pdf.body(
        "This is where SHAP comes in. SHAP is based on game theory (specifically "
        "Shapley values from cooperative game theory, 1953) and provides a "
        "mathematically rigorous way to attribute each feature's contribution "
        "to a specific prediction."
    )

    pdf.section_title("3.2", "How SHAP Works (Intuition)")
    pdf.body(
        "Imagine you're splitting a restaurant bill fairly among friends who "
        "ordered different items. Shapley values solve this exact problem: "
        "they compute each player's fair contribution by considering all "
        "possible orderings of players."
    )
    pdf.body("For ML, 'players' are features and the 'bill' is the prediction:")
    pdf.numbered(1, "Start with the base prediction (average model output)")
    pdf.numbered(2, "For each feature, compute: 'How much does the prediction "
                 "change when I add this feature, across all possible combinations "
                 "of other features?'")
    pdf.numbered(3, "The result is each feature's SHAP value - positive means "
                 "it pushed the prediction higher, negative means lower")
    pdf.ln(2)

    pdf.tip_box(
        "The Additivity Property",
        "SHAP values have a beautiful property: they always sum to the difference "
        "between the prediction and the base value. If base = 0.3 and prediction = 0.87, "
        "the 8 SHAP values will sum to exactly 0.57. This makes explanations consistent "
        "and trustworthy."
    )

    pdf.section_title("3.3", "Local vs Global Explanations")
    pdf.subsection("Local: Per-Session")
    pdf.body(
        "A local explanation answers: 'For THIS specific session, which features "
        "drove the prediction?' For example:"
    )
    pdf.code_block(
        "Session #42 - Friction probability: 0.87\n"
        "  checkout_hesitation_s = 45.0  [SHAP: +0.32]  increases_risk\n"
        "  rage_click_score = 0.6        [SHAP: +0.21]  increases_risk\n"
        "  session_duration_s = 30.0     [SHAP: -0.08]  decreases_risk"
    )
    pdf.body(
        "This tells us: 'Session #42 has high friction mainly because of 45 seconds "
        "of checkout hesitation and a rage click score of 0.6.'"
    )

    pdf.subsection("Global: Across All Sessions")
    pdf.body(
        "A global explanation answers: 'Across all sessions, which features "
        "matter most?' This is computed as the mean absolute SHAP value across "
        "a dataset. It tells you which features the model relies on most heavily."
    )

    pdf.section_title("3.4", "Risk Direction Logic")
    pdf.body(
        "A subtle but critical detail: the meaning of a positive SHAP value "
        "depends on which model you're explaining:"
    )
    pdf.table(
        ["Model", "Positive SHAP Means", "Risk Direction"],
        [
            ["Conversion", "Higher purchase probability", "DECREASES risk"],
            ["Friction", "Higher friction probability", "INCREASES risk"],
            ["Intent", "Higher predicted-class probability", "Depends on class"],
        ],
        [40, 70, 80],
    )
    pdf.body(
        "The UnifiedExplainer handles this automatically via a direction map, "
        "so the FeatureAttribution.direction field always tells you whether "
        "a feature 'increases_risk' or 'decreases_risk' regardless of which "
        "model generated the SHAP values."
    )

    pdf.section_title("3.5", "Implementation (CONV-23)")
    pdf.body("Files: ml/src/explainability/shap_explainer.py + modifications to training scripts")
    pdf.code_block(
        "from src.explainability.shap_explainer import UnifiedExplainer\n\n"
        "explainer = UnifiedExplainer.from_artifacts(Path('ml/artifacts'))\n\n"
        "# Local explanation for one session\n"
        "local = explainer.explain_local(features, 'friction', top_k=3)\n"
        "for attr in local.top_k:\n"
        "    print(f'{attr.feature_name}: {attr.shap_value} ({attr.direction})')\n\n"
        "# Global explanation across a dataset\n"
        "glob = explainer.explain_global(X_test, 'conversion')\n"
        "print(glob.feature_ranking)  # ['checkout_hesitation_s', ...]"
    )

    pdf.warn_box(
        "Multi-Class SHAP Gotcha",
        "For the intent classifier (4 classes), SHAP returns values per class. Newer "
        "versions of SHAP return a 3D array (samples x features x classes) while older "
        "versions return a list of 2D arrays. Our UnifiedExplainer handles both formats "
        "automatically. When writing your own SHAP code, always check the shape!"
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 4: Intervention Engine
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("4", "Psychology-Aware Interventions")

    pdf.section_title("4.1", "Bridging ML and Business Action")
    pdf.body(
        "This is where EmoraTest's true value proposition lives. Many ML "
        "systems stop at prediction: 'this user will abandon with 73% probability.' "
        "But a merchant can't act on that number. They need to know WHAT to do."
    )
    pdf.body(
        "The Intervention Engine bridges this gap by connecting SHAP explanations "
        "to the psychology framework. It answers: 'Given that checkout_hesitation "
        "and price_dwell are driving this session's friction, the user is likely "
        "experiencing Loss Aversion - show them a money-back guarantee.'"
    )

    pdf.section_title("4.2", "Two-Layer Matching Logic")
    pdf.body("The engine uses two complementary layers to determine interventions:")
    pdf.subsection("Layer 1: Rule-Based Trigger Matching")
    pdf.body(
        "Each psychological state in the framework has trigger conditions. For example, "
        "Loss Aversion triggers when checkout_hesitation_s >= 15 AND price_dwell_time_s >= 10. "
        "The engine evaluates these conditions against the session's actual features."
    )
    pdf.body(
        "The trigger_logic field controls how conditions combine: 'ALL' means every "
        "condition must be true (AND logic). 'ANY' means at least one condition "
        "must be true (OR logic). UI Frustration uses ANY - either rage clicks "
        "OR erratic mouse movement is enough to trigger it."
    )

    pdf.subsection("Layer 2: SHAP-Enhanced Confidence")
    pdf.body(
        "Here's the clever part: just because a feature crosses a threshold "
        "doesn't mean the ML model actually relied on it. A session might have "
        "high checkout_hesitation (triggering Loss Aversion rules) but the "
        "friction model might have scored it as high-friction mainly because "
        "of rage_clicks, not checkout_hesitation."
    )
    pdf.body(
        "SHAP-enhanced confidence solves this. When SHAP attributions are "
        "provided, the engine checks: 'Did the trigger features also have "
        "high SHAP values?' If yes, confidence gets a boost (up to +0.2). "
        "This means the ML model AGREES with the psychology framework's "
        "assessment, making the intervention more reliable."
    )

    pdf.section_title("4.3", "Priority Scoring")
    pdf.body(
        "When multiple psychological states are triggered (common for high-friction "
        "sessions), the engine must decide which interventions to show. Showing "
        "5 different popups would be worse than showing none. The priority formula is:"
    )
    pdf.code_block(
        "priority_score = severity_weight * confidence * expected_lift"
    )
    pdf.body(
        "This naturally surfaces the most impactful interventions. A high-severity "
        "state (Abandonment Intent: 0.95) with high confidence and a high-lift "
        "intervention (exit discount: 22% expected lift) will always rank above "
        "a lower-severity state with a modest intervention."
    )

    pdf.section_title("4.4", "The 8 Psychological States")
    pdf.table(
        ["State", "Severity", "Trigger Logic", "Key Triggers"],
        [
            ["Abandonment Intent", "0.95", "ANY", "exit_intent >= 2 OR duration <= 120"],
            ["UI Frustration", "0.90", "ANY", "rage_click >= 0.3 OR velocity >= 100k"],
            ["Loss Aversion", "0.85", "ALL", "checkout_hes >= 15 AND price_dwell >= 10"],
            ["Trust Gap", "0.80", "ALL", "price_dwell >= 8 AND checkout_hes >= 20"],
            ["Price Shock", "0.75", "ALL", "price_dwell >= 15 AND checkout_hes <= 5"],
            ["Approach-Avoidance", "0.72", "ALL", "hesitation >= 0.3 AND exit >= 1 AND retreat >= 2"],
            ["Decision Fatigue", "0.70", "ALL", "duration >= 300 AND retreat >= 5"],
            ["Decision Uncertainty", "0.65", "ALL", "hesitation >= 0.4 AND retreat >= 3"],
        ],
        [42, 20, 27, 101],
    )

    pdf.section_title("4.5", "Implementation (CONV-24)")
    pdf.body("File: ml/src/intervention/engine.py")
    pdf.code_block(
        "from src.intervention.engine import InterventionEngine\n\n"
        "engine = InterventionEngine()\n"
        "features = {'checkout_hesitation_s': 25.0, 'price_dwell_time_s': 12.0, ...}\n\n"
        "# Match psychological states\n"
        "states = engine.match_states(features, shap_attributions)\n"
        "for s in states:\n"
        "    print(f'{s.state_label}: confidence={s.confidence}')\n\n"
        "# Get ranked interventions\n"
        "recs = engine.recommend(features, shap_attributions, max_interventions=3)\n"
        "for r in recs:\n"
        "    print(f'{r.intervention_id}: {r.message} (lift: {r.expected_lift})')"
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 5: Scoring Service
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("5", "Real-Time Scoring Service")

    pdf.section_title("5.1", "The Orchestration Challenge")
    pdf.body(
        "We now have 4 separate components: 3 ML models, an ensemble combiner, "
        "a SHAP explainer, and an intervention engine. The scoring service's job "
        "is to orchestrate them into a single, fast, easy-to-use API."
    )
    pdf.body("For each session, the service executes this pipeline:")
    pdf.numbered(1, "Convert feature dict to ordered numpy array (matching FEATURE_COLS)")
    pdf.numbered(2, "Run conversion predictor -> purchase probability")
    pdf.numbered(3, "Run intent classifier -> intent label + class probabilities")
    pdf.numbered(4, "Run friction detector -> friction probability")
    pdf.numbered(5, "Run ensemble -> unified session score + action + confidence")
    pdf.numbered(6, "Run SHAP on all 3 models (optional, for explainability)")
    pdf.numbered(7, "Run intervention engine -> matched states + ranked recommendations")
    pdf.numbered(8, "Package everything into a ScoringResult with latency tracking")
    pdf.ln(2)

    pdf.section_title("5.2", "Design Decisions")
    pdf.subsection("Singleton Pattern")
    pdf.body(
        "Loading 3 XGBoost models + 3 SHAP explainers from disk takes ~200ms. "
        "We can't afford this per request. The ScoringService uses a singleton "
        "pattern (get_instance()) so models are loaded once at startup and "
        "reused for every subsequent request."
    )

    pdf.subsection("explain=True/False Toggle")
    pdf.body(
        "SHAP computation adds ~50-100ms per session. For real-time scoring "
        "(single session, user-facing), we want full explanations. For batch "
        "scoring (model evaluation, data pipeline), we skip SHAP for speed. "
        "The explain parameter controls this."
    )

    pdf.subsection("Feature Dict Reordering")
    pdf.body(
        "XGBoost is sensitive to feature order - the features must be in the "
        "same order as during training. Callers might pass features in any "
        "order. The service internally reorders them to match FEATURE_COLS, "
        "preventing subtle prediction errors."
    )

    pdf.section_title("5.3", "The ScoringResult Object")
    pdf.body("Every call to score_session returns a ScoringResult containing:")
    pdf.table(
        ["Field", "Type", "Description"],
        [
            ["session_score", "float", "Unified abandonment risk 0-1"],
            ["recommended_action", "str", "monitor/nudge/intervene/urgent"],
            ["confidence", "float", "Model agreement confidence 0-1"],
            ["conversion_prob", "float", "Purchase probability 0-1"],
            ["intent_label", "str", "Predicted intent class"],
            ["intent_probs", "dict", "Per-class probabilities"],
            ["friction_prob", "float", "Friction probability 0-1"],
            ["top_shap_features", "dict", "Top-3 SHAP per model"],
            ["interventions", "list", "Ranked InterventionRecommendations"],
            ["psychological_states", "list", "Matched PsychologicalStateMatch"],
            ["latency_ms", "float", "End-to-end scoring time in ms"],
        ],
        [45, 25, 120],
    )

    pdf.section_title("5.4", "Implementation (CONV-25)")
    pdf.body("File: ml/src/scoring/service.py")
    pdf.code_block(
        "from src.scoring.service import ScoringService\n\n"
        "# Load models once\n"
        "service = ScoringService.get_instance(\n"
        "    artifacts_dir='ml/artifacts'\n"
        ")\n\n"
        "# Score a session\n"
        "result = service.score_session({\n"
        "    'hesitation_score': 0.4,\n"
        "    'price_dwell_time_s': 12.0,\n"
        "    'rage_click_score': 0.1,\n"
        "    'scroll_retreat_count': 3,\n"
        "    'exit_intent_count': 1,\n"
        "    'checkout_hesitation_s': 18.0,\n"
        "    'velocity_variance': 50000.0,\n"
        "    'session_duration_s': 200.0,\n"
        "})\n\n"
        "print(f'Risk: {result.session_score} -> {result.recommended_action}')\n"
        "print(f'Latency: {result.latency_ms}ms')\n"
        "for iv in result.interventions:\n"
        "    print(f'  -> {iv.intervention_id}: {iv.message}')"
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 6: Evaluation & A/B Testing
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("6", "Model Evaluation & A/B Testing")

    pdf.section_title("6.1", "Why Standard Accuracy Isn't Enough")
    pdf.body(
        "With a 4% conversion rate, a model that ALWAYS predicts 'abandon' "
        "would have 96% accuracy. Clearly, accuracy alone is misleading for "
        "imbalanced datasets. That's why we track multiple metrics:"
    )
    pdf.bullet("AUC-ROC: How well can the model distinguish classes at all thresholds?")
    pdf.bullet("AUC-PR: Precision-recall curve area, better for imbalanced data")
    pdf.bullet("F1 Score: Harmonic mean of precision and recall")
    pdf.bullet("Per-class metrics: Because overall metrics hide class-specific failures")

    pdf.section_title("6.2", "Comparing Model Versions")
    pdf.body(
        "When you train a new model version (e.g., predictor_v2 with different "
        "hyperparameters), you need to know if it's ACTUALLY better, not just "
        "luckier on this particular test set. The ModelComparator uses "
        "McNemar's test - a statistical test specifically designed for "
        "comparing paired classifiers."
    )
    pdf.subsection("McNemar's Test (Intuition)")
    pdf.body(
        "McNemar's test only looks at disagreements between the two models. "
        "If model A gets sample #42 right but model B gets it wrong (or vice "
        "versa), those are the informative cases. If both agree, it doesn't "
        "tell us which is better. The test asks: 'Are the disagreements "
        "symmetric, or does one model consistently win?'"
    )

    pdf.section_title("6.3", "A/B Testing Interventions")
    pdf.body(
        "The ABTestAnalyzer computes statistical significance for intervention "
        "experiments. When you run an A/B test (control: no intervention vs "
        "treatment: show money-back guarantee), it tells you:"
    )
    pdf.bullet("Is the conversion rate difference statistically significant? (two-proportion z-test)")
    pdf.bullet("What is the lift? (percentage improvement)")
    pdf.bullet("Do you have enough data? (minimum sample size calculation)")

    pdf.tip_box(
        "Sample Size Matters",
        "A common mistake is stopping A/B tests too early. With n=50 per group, "
        "you can't reliably detect effects smaller than ~15%. For a typical 4% "
        "baseline with 2% MDE (minimum detectable effect), you need ~2,000 sessions "
        "per variant. The required_sample_size() method computes this for you."
    )

    pdf.section_title("6.4", "Implementation (CONV-26)")
    pdf.body("Files: ml/src/evaluation/metrics.py and ml/src/evaluation/comparison.py")
    pdf.code_block(
        "from src.evaluation.metrics import evaluate_binary\n"
        "from src.evaluation.comparison import ABTestAnalyzer\n\n"
        "# Evaluate a model\n"
        "metrics = evaluate_binary(y_true, y_pred, y_proba)\n"
        "print(f'AUC: {metrics.auc_roc}, F1: {metrics.f1}')\n\n"
        "# Analyze an A/B test\n"
        "ab = ABTestAnalyzer()\n"
        "result = ab.analyze(\n"
        "    control_conversions=100, control_total=1000,\n"
        "    treatment_conversions=150, treatment_total=1000,\n"
        ")\n"
        "print(f'Lift: {result.lift:.1%}, p={result.p_value:.4f}')\n"
        "# Lift: 50.0%, p=0.0007 -> statistically significant!"
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 7: Integration Testing
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("7", "Integration Testing: Validating the Pipeline")

    pdf.section_title("7.1", "Why Integration Tests Matter")
    pdf.body(
        "Unit tests verify each component in isolation: the ensemble math is "
        "correct, the SHAP explainer returns the right shape, the intervention "
        "engine matches the right states. But components that work individually "
        "can fail when combined. Integration tests catch these failures."
    )
    pdf.body("Common integration failures we test for:")
    pdf.bullet("Feature column mismatch: model trained on features in order A, "
               "service passes them in order B")
    pdf.bullet("Type mismatches: ensemble expects float but gets numpy.float64")
    pdf.bullet("SHAP format changes: newer library version returns different shapes")
    pdf.bullet("Intervention IDs don't match framework: engine recommends an "
               "intervention that doesn't exist in the JSON")

    pdf.section_title("7.2", "Scenario-Based Tests")
    pdf.body(
        "The most valuable integration tests are scenario-based: they simulate "
        "a realistic user session and verify the entire pipeline produces "
        "sensible results. Here are the key scenarios we test:"
    )
    pdf.subsection("Scenario: High Friction User")
    pdf.body(
        "Features: rage_click=0.6, velocity_variance=200000. Expected: "
        "UI Frustration state triggered, 'live_help' or 'report_issue' "
        "intervention recommended."
    )
    pdf.subsection("Scenario: Loss Aversion Shopper")
    pdf.body(
        "Features: checkout_hesitation=25s, price_dwell=15s. Expected: "
        "Loss Aversion state triggered, 'money_back_guarantee' recommended."
    )
    pdf.subsection("Scenario: Happy Browser")
    pdf.body(
        "Features: all low signals. Expected: no states triggered, "
        "action='monitor', no interventions."
    )

    pdf.section_title("7.3", "Cross-Component Contract Tests")
    pdf.body("These tests verify that components agree on shared contracts:")
    pdf.bullet("All 3 model metadata files reference the exact same FEATURE_COLS")
    pdf.bullet("All .pkl artifacts can be loaded without errors")
    pdf.bullet("Session scores are always in [0, 1] even for extreme inputs")
    pdf.bullet("Every intervention_id in recommendations exists in framework_v1.json")
    pdf.bullet("Batch scoring produces identical results to individual scoring")

    pdf.section_title("7.4", "Test Results")
    pdf.body("All 145 tests pass (90 from Epic 2 + 55 from Epic 1):")
    pdf.table(
        ["Test File", "Tests", "Status"],
        [
            ["test_ensemble.py", "21", "PASS"],
            ["test_shap_explainer.py", "14", "PASS"],
            ["test_intervention_engine.py", "14", "PASS"],
            ["test_scoring_service.py", "15", "PASS"],
            ["test_evaluation.py", "14", "PASS"],
            ["test_integration_pipeline.py", "12", "PASS"],
            ["Epic 1 tests (unchanged)", "55", "PASS"],
        ],
        [70, 30, 90],
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 8: Architecture
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("8", "Architecture & Data Flow")

    pdf.section_title("8.1", "Module Dependency Graph")
    pdf.body("The Epic 2 modules are organized in a clean dependency hierarchy:")
    pdf.code_block(
        "ml/src/\n"
        "  data/loader.py          <- FEATURE_COLS definition (shared constant)\n"
        "  features/extraction.py  <- Raw events -> 8 features\n"
        "  training/               <- Train & save models (+ SHAP explainers)\n"
        "    train_xgboost.py\n"
        "    train_intent.py\n"
        "    train_friction.py\n"
        "  ensemble/ensemble.py    <- Weighted model combination (CONV-22)\n"
        "  explainability/         <- SHAP wrapper for all models (CONV-23)\n"
        "    shap_explainer.py\n"
        "  intervention/engine.py  <- Psychology framework matching (CONV-24)\n"
        "  evaluation/             <- Metrics & comparison (CONV-26)\n"
        "    metrics.py\n"
        "    comparison.py\n"
        "  scoring/service.py      <- Orchestrator (CONV-25) depends on all above"
    )

    pdf.section_title("8.2", "Data Flow: Session Scoring")
    pdf.body("When a session is scored, data flows through this pipeline:")
    pdf.code_block(
        "Browser Events\n"
        "     |\n"
        "     v\n"
        "[Feature Extraction] -> 8 behavioral features\n"
        "     |\n"
        "     v\n"
        "[3 XGBoost Models] -> conversion_prob, intent_label, friction_prob\n"
        "     |                      |\n"
        "     v                      v\n"
        "[Ensemble Combiner]  [SHAP Explainer]\n"
        "     |                      |\n"
        "     v                      v\n"
        "session_score +      feature attributions\n"
        "action_label              |\n"
        "     |                    v\n"
        "     |            [Intervention Engine]\n"
        "     |                    |\n"
        "     v                    v\n"
        "[ScoringResult] = score + action + SHAP + interventions"
    )

    pdf.section_title("8.3", "File Summary")
    pdf.table(
        ["File", "Story", "Purpose"],
        [
            ["ensemble/ensemble.py", "CONV-22", "Weighted model combiner + action ladder"],
            ["explainability/shap_explainer.py", "CONV-23", "Unified SHAP for all 3 models"],
            ["training/train_xgboost.py", "CONV-23", "Added SHAP explainer saving"],
            ["training/train_intent.py", "CONV-23", "Added SHAP explainer saving"],
            ["intervention/engine.py", "CONV-24", "Psychology state matching + ranking"],
            ["scoring/service.py", "CONV-25", "Singleton orchestrator service"],
            ["evaluation/metrics.py", "CONV-26", "Binary + multiclass eval metrics"],
            ["evaluation/comparison.py", "CONV-26", "Model comparison + A/B analysis"],
            ["tests/test_integration_pipeline.py", "CONV-27", "End-to-end pipeline tests"],
        ],
        [62, 22, 106],
    )

    # ══════════════════════════════════════════════════════════
    # CHAPTER 9: Exercises
    # ══════════════════════════════════════════════════════════
    pdf.chapter_title("9", "Exercises & Challenges")

    pdf.body(
        "These exercises will deepen your understanding of the concepts "
        "covered in this guide. They range from beginner (modify existing "
        "code) to advanced (design new features)."
    )

    pdf.section_title("9.1", "Beginner Exercises")
    pdf.numbered(1, "Weight Ablation: Modify EnsembleConfig to set intent_weight=0 and "
                 "re-run the ensemble tests. What changes? Why might you want to "
                 "disable the intent signal for some merchants?")
    pdf.numbered(2, "New Threshold: Add a 5th action level 'critical' at score >= 0.90. "
                 "Update ACTION_THRESHOLDS and add a test for it.")
    pdf.numbered(3, "Top-K SHAP: Change the default top_k from 3 to 5 in the "
                 "scoring service. Run the tests - do they still pass? Why or why not?")

    pdf.section_title("9.2", "Intermediate Exercises")
    pdf.numbered(4, "Custom Psychology State: Add a 9th psychological state to "
                 "framework_v1.json called 'Social Comparison' that triggers when "
                 "session_duration >= 400 AND scroll_retreat >= 8. Create appropriate "
                 "interventions and verify the engine detects it.")
    pdf.numbered(5, "SHAP Waterfall: Write a function that takes a LocalExplanation "
                 "and produces a text-based waterfall chart showing how each feature "
                 "pushes the prediction from base_value to the final prediction.")
    pdf.numbered(6, "Batch Evaluation: Use the evaluation framework to compare "
                 "predictor_v1 against a model trained with different hyperparameters "
                 "(e.g., max_depth=4 instead of 6). Is the difference significant?")

    pdf.section_title("9.3", "Advanced Challenges")
    pdf.numbered(7, "Stacking Ensemble: Replace the weighted combination with a "
                 "logistic regression meta-model that takes the 3 model outputs as "
                 "features. Does it outperform the weighted approach? (Hint: you'll "
                 "need a held-out fold for generating meta-features.)")
    pdf.numbered(8, "Temporal SHAP: The current SHAP explains a snapshot. Design a "
                 "system that tracks SHAP values over time within a session and "
                 "triggers interventions when a feature's attribution crosses a "
                 "threshold (e.g., 'checkout_hesitation SHAP just jumped from 0.1 to 0.4').")
    pdf.numbered(9, "Multi-Armed Bandit: Replace the fixed intervention ranking "
                 "with a Thompson Sampling bandit that learns which interventions "
                 "work best for each psychological state, adapting in real time.")

    # ══════════════════════════════════════════════════════════
    # Final page
    # ══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*CoursePDF.PRIMARY)
    pdf.cell(0, 12, "Summary", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*CoursePDF.DARK)
    pdf.multi_cell(0, 6,
        "Epic 2 transformed three independent ML models into an integrated "
        "intelligence system. The ensemble combines their predictions into a "
        "unified risk score. SHAP explains WHY each prediction was made. The "
        "intervention engine maps those explanations to psychology-backed "
        "recommendations. And the scoring service orchestrates it all in "
        "real-time, ready for the backend API to call.\n\n"
        "This architecture is intentionally modular: each component can be "
        "tested, upgraded, or replaced independently. The psychology framework "
        "is a JSON file, not hardcoded logic. The ensemble weights are "
        "configurable. The SHAP layer handles multiple model formats "
        "transparently.\n\n"
        "Next up: Epic 3 (JavaScript SDK) will capture browser events, "
        "Epic 4 (Backend API) will expose the scoring service via REST "
        "endpoints, and Epic 5 (Dashboard) will visualize everything for "
        "merchants.",
        align="C",
    )

    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*CoursePDF.PRIMARY)
    pdf.cell(0, 8, "Statistics", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*CoursePDF.DARK)
    stats = [
        "6 stories implemented (CONV-22 to CONV-27)",
        "5 new modules: ensemble, explainability, intervention, scoring, evaluation",
        "2 existing training scripts enhanced with SHAP",
        "90 new tests (145 total with Epic 1)",
        "0 regressions",
    ]
    for s in stats:
        pdf.cell(0, 6, f"  -  {s}", new_x="LMARGIN", new_y="NEXT")

    # Save
    output_path = "docs/Epic2_ML_Ensemble_SHAP.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_pdf()
