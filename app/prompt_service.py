from typing import Literal

PromptStyle = Literal["zero_shot", "few_shot", "role_based"]

class PromptService:
    @staticmethod
    def build_prompt(question: str, context: str, style: PromptStyle = "zero_shot") -> str:

        if style == "zero_shot":
            return f"""Answer the user's question using ONLY the retrieved context below.

RETRIEVED CONTEXT

{context}

USER QUESTION

{question}

Rules:
1. Do not invent facts not present in context.
2. If not enough info, say: "I could not find enough information in the supplied documents."
3. Keep answer factual and concise.
Answer:"""

        elif style == "few_shot":
            
            return f"""You answer questions based on technical documents. Follow the example format exactly - cite filename.

Example 1 - Deep Learning:
Context: [SOURCE 1] File: deep_learning.pdf Page: 2... CNNs use convolutional layers with filters to detect spatial features in images. Pooling layers reduce dimensionality.
Question: What do convolutional layers do in CNNs?
Answer: According to deep_learning.pdf (Page 2), convolutional layers use filters to detect spatial features in images, and pooling layers reduce dimensionality.

Example 2 - Machine Learning:
Context: [SOURCE 1] File: ml_basics.pdf Page: 5... Overfitting occurs when model memorizes training data and fails to generalize. Solution is dropout and cross-validation.
Question: What is overfitting?
Answer: Based on ml_basics.pdf (Page 5), overfitting occurs when a model memorizes training data and fails to generalize, with solutions like dropout and cross-validation.

Example 3 - Green Solutions:
Context: [SOURCE 1] File: green_solutions.pdf Page: 1... Solar panels convert sunlight to electricity with 20-22% efficiency. Excess energy can be stored in lithium-ion batteries.
Question: What is efficiency of solar panels?
Answer: According to green_solutions.pdf (Page 1), solar panels convert sunlight to electricity with 20-22% efficiency and excess energy can be stored in lithium-ion batteries.

Now your turn:
RETRIEVED CONTEXT

{context}

USER QUESTION

{question}

Answer with citations like examples above:"""

        elif style == "role_based":
            return f"""You are a Technical Document Analyst specializing in Machine Learning, Deep Learning, and Green Technologies.

Your expertise:
- Deep Learning: Neural networks, CNN, RNN, Transformers
- Machine Learning: Supervised/Unsupervised, Overfitting, Embeddings
- Green Solutions: Solar, Sustainability, Energy Efficiency

Instructions:
1. Analyze context thoroughly - focus on technical accuracy.
2. Provide structured answer with bullet points.
3. Explain concepts clearly as an analyst.
4. Always cite File name, Page at end.
5. If context lacks info, state it.

RETRIEVED CONTEXT

{context}

TASK

Question: {question}

As a Technical Document Analyst, provide your analysis:"""