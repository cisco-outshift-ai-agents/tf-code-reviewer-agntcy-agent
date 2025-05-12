# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableSerializable
from app.models.models import ReviewComments


def create_code_reviewer_chain(model: BaseChatModel, ) -> RunnableSerializable[dict, dict | ReviewComments]:
    llm_with_structured_output = model.with_structured_output(ReviewComments)

    # If some lines are indented more than others, dedent can't normalize it effectively.
    system_message = SystemMessagePromptTemplate.from_template("""
            You are an expert in Terraform and a diligent code reviewer.
            Your goal is to support the developer in writing safer, cleaner, and more maintainable Terraform code.
            Provide your feedback in a clear, concise, constructive, professional with explicit details.
            """)

    user_message = HumanMessagePromptTemplate.from_template("""
        You will be given context_files, changed files and the static analyzer output.
        class codeReviewInput(BaseModel):
    
    context_files description : 
            A list of all the Terraform files. The context file have following format:
                - path: the file name
                - content: the original content of the file
    
    changed_files description: 
            List of code changes across Terraform files. The changes have the following format:
            - filename: the name of the file where the change was done
            - start_line: the line number where the change was added
            - changed_code: the code that was removed/added after the start line, there's a + or - sign at the beginning of every change line, it indicates if it was added or removed, ignore this sign.
            - status: indicates if the changed_code was added/removed
            - Changes with "removed" status mean that the code in that change was deleted from the codebase, it's not part of the code anymore.
            - Changes with "added" status mean that the code in that change was added the codebase.
            - Always focus on whether a change was added or removed from the codebase. If it was removed then that code is not part of the codebase anymore.
            - Sometimes the changes are in pairs, one change with a 'removed' status and one with 'added', but they belong together, even when their line numbers are far apart.
            Identify these pairs and DO NOT add the same comment to the removed and added part twice!
    
    static_analyzer_output description:
        - A list of multiple static code analyzers (tflint, tfsec, etc.) on the new code.
        - The static_analyzer_output could be useful for understanding the potential issues introduced by the user, like missing references, undefined or unused variables etc.
        - The static_analyzer_output could have issues which are not related to the current code changes, you MUST ignore these issues as they weren't introduced by this PR.

        Input:
            context_filesfiles : {context_files}
            changed_files: {changes}
            static_analyzer_output: {static_analyzer_output}


        Provide feedback based on the following best-practice categories:
            1. **Security**: Secrets management, IAM roles/policies, network configurations, etc.
            2. **Maintainability**: Code organization, DRY principle, module usage, variable naming, version pinning.
            3. **Scalability & Performance**: Resource sizing, autoscaling configurations, load balancing.
            4. **Reliability**: Redundancy, high availability, state management strategies (e.g., remote state with locking).
            5. **Cost Optimization**: Potential oversizing of resources, recommended resource types for cost efficiency.
            6. **Compliance & Governance**: Adherence to organizational policies, tagging conventions, regulatory requirements.
            7. **Documentation & Observability**: Comments, usage docs, logging/monitoring configuration.
            For each category, list:
            - **Strengths** and **Areas of Improvement**
            - **Suggested changes** or additional best practices to consider


        Here are some guidelines on providing feedback:
        - Review all the files to understand the current state of the codebase.
        - Review the changes to understand what was changed in this PR to arrive at the current state of the files.
        - Always check the changes in the CHANGES list and comment only on the changed lines. You MUST NOT comment on unchanged code.
        - Check the status of the changes and comment accordingly. For eg., if the status says 'added' then that piece of code was a new addition and if it says 'removed' then it was deleted from the codebase.
        - You DO NOT have to comment on every code change block, if you do not see an issue, or if you already commented on the other pair of the change, ignore and move on.
        - Each comment MUST refer to a change and the change must be associated with the issue that the comment is mentioning.
        - ONLY comment on changes that have actual code changes (e.g., variable definitions, resource definitions, etc.)
        - DO NOT provide general or positive feedback (e.g., 'This looks good', 'This is a best practice', etc.)
        - Use the static_analyzer_output to identify potential errors in the new code.
        - Your comments should be brief, explicit, clear and professional

        Before returning your response, take your time to review your results:
        - Make sure that each comment belongs to a change.
        - Make sure the properties of the comment are aligned with the change object's properties.
        - Make sure the comment messages are relevant and provide actionable items to the user.
        - Make sure you checked the static analyzer outputs.
            """)

    messages = [system_message, user_message]
    prompt = ChatPromptTemplate.from_messages(messages)
    return prompt | llm_with_structured_output
