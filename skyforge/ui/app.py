# Copyright (c) Alibaba, Inc. and its affiliates.
import os
from functools import partial
from typing import List, Optional, Union

import gradio as gr
from packaging import version
from transformers.utils import strtobool

import swift
from swift.llm import (DeployArguments, EvalArguments, ExportArguments, RLHFArguments, SamplingArguments, SwiftPipeline,
                       WebUIArguments)
from swift.ui.llm_eval.llm_eval import LLMEval
from swift.ui.llm_export.llm_export import LLMExport
from swift.ui.llm_grpo.llm_grpo import LLMGRPO
from swift.ui.llm_infer.llm_infer import LLMInfer
from swift.ui.llm_rlhf.llm_rlhf import LLMRLHF
from swift.ui.llm_sample.llm_sample import LLMSample
from swift.ui.llm_train.llm_train import LLMTrain

locale_dict = {
    'title': {
        'zh': '✨ AI魔法工坊 ✨',
        'en': '✨ AI Magic Workshop ✨'
    },
    'sub_title': {
        'zh':
        '欢迎来到魔法工坊，开始你的AI创造之旅吧！',
        'en':
        'Welcome to the Magic Workshop, start your AI creation journey!',
    },
    'star_beggar': {
        'zh':
        '觉得好玩就给我们点个赞吧 💖',
        'en':
        'Give us a like if you enjoy it 💖'
    },
}


class SwiftWebUI(SwiftPipeline):

    args_class = WebUIArguments
    args: args_class

    def run(self):
        lang = os.environ.get('SWIFT_UI_LANG') or self.args.lang
        share_env = os.environ.get('WEBUI_SHARE')
        share = strtobool(share_env) if share_env else self.args.share
        server = os.environ.get('WEBUI_SERVER') or self.args.server_name
        port_env = os.environ.get('WEBUI_PORT')
        port = int(port_env) if port_env else self.args.server_port
        LLMTrain.set_lang(lang)
        LLMRLHF.set_lang(lang)
        LLMGRPO.set_lang(lang)
        LLMInfer.set_lang(lang)
        LLMExport.set_lang(lang)
        LLMEval.set_lang(lang)
        LLMSample.set_lang(lang)
        # Define custom CSS for sidebar layout
        custom_css = """
        .gradio-container {
            max-width: 100% !important;
        }
        #sidebar {
            background-color: #f7f9fc;
            padding: 30px 20px;
            border-right: 1px solid #eef2f6;
            min-height: 100vh;
        }
        #content {
            padding: 30px;
            background-color: #ffffff;
        }
        /* Hide top-level tabs if they somehow appear */
        #content > .tabs > .tab-nav {
            display: none !important;
        }
        
        /* Sidebar Menu Styling */
        .sidebar-menu {
            display: flex !important;
            flex-direction: column !important;
            gap: 12px !important;
        }
        /* Target the internal wrapper if present */
        .sidebar-menu > .wrap {
            display: flex !important;
            flex-direction: column !important;
            gap: 12px !important;
        }
        .sidebar-menu label {
            width: 100% !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            transition: all 0.3s ease !important;
            background: white !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
            display: flex !important;
            align-items: center !important;
            margin-right: 0 !important;
            margin-bottom: 0 !important;
        }
        .sidebar-menu label:hover {
            border-color: #7f6df2 !important;
            background: #f8f7ff !important;
            transform: translateX(5px);
        }
        .sidebar-menu label.selected {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3) !important;
        }
        .sidebar-menu label span {
            font-weight: 500 !important;
            font-size: 1.05em !important;
        }
        
        /* Hide the radio circle */
        .sidebar-menu input[type="radio"] {
            display: none;
        }
        """

        with gr.Blocks(title='AI Magic Workshop', theme=gr.themes.Ocean(), css=custom_css) as app:
            try:
                _version = swift.__version__
            except AttributeError:
                _version = ''
            
            tabs = [LLMTrain, LLMRLHF, LLMGRPO, LLMInfer, LLMExport, LLMEval, LLMSample]
            tab_labels = [tab.locale_dict[tab.group]['label'][lang] for tab in tabs]
            tab_ids = [tab.group for tab in tabs]
            label_to_id = dict(zip(tab_labels, tab_ids))
            
            # Hijack Logic
            original_tab_item = gr.TabItem
            main_columns = []
            
            class HijackTabItem:
                def __init__(self, *args, **kwargs):
                    self.elem_id = kwargs.get('elem_id')
                    # Only hijack the main tabs defined in tab_ids
                    if self.elem_id in tab_ids:
                        visible = (self.elem_id == tab_ids[0])
                        self.container = gr.Column(visible=visible, elem_id=self.elem_id)
                        main_columns.append(self.container)
                    else:
                        self.container = original_tab_item(*args, **kwargs)

                def __enter__(self):
                    return self.container.__enter__()

                def __exit__(self, *args):
                    return self.container.__exit__(*args)

            # Apply Hijack
            gr.TabItem = HijackTabItem

            with gr.Row():
                with gr.Column(scale=1, elem_id="sidebar"):
                    gr.HTML(f"<h2>{locale_dict['title'][lang]}</h2>")
                    gr.HTML(f"<p>{locale_dict['sub_title'][lang]}</p>")
                    
                    menu = gr.Radio(
                        choices=tab_labels,
                        value=tab_labels[0],
                        label="Menu",
                        interactive=True,
                        container=False,
                        elem_classes=["sidebar-menu"]
                    )

                with gr.Column(scale=4, elem_id="content"):
                    # Build UIs directly in the content column
                    # The hijacked TabItem will create columns instead of tabs for these
                    LLMTrain.build_ui(LLMTrain)
                    LLMRLHF.build_ui(LLMRLHF)
                    LLMGRPO.build_ui(LLMGRPO)
                    LLMInfer.build_ui(LLMInfer)
                    LLMExport.build_ui(LLMExport)
                    LLMEval.build_ui(LLMEval)
                    LLMSample.build_ui(LLMSample)
            
            # Restore TabItem immediately after building
            gr.TabItem = original_tab_item

            def switch_tab(label):
                target_id = label_to_id[label]
                updates = []
                for col in main_columns:
                    # Update visibility based on whether this column matches the target
                    is_visible = (col.elem_id == target_id)
                    updates.append(gr.update(visible=is_visible))
                return updates

            menu.change(fn=switch_tab, inputs=[menu], outputs=main_columns)

            concurrent = {}
            if version.parse(gr.__version__) < version.parse('4.0.0'):
                concurrent = {'concurrency_count': 5}
            app.load(
                partial(LLMTrain.update_input_model, arg_cls=RLHFArguments),
                inputs=[LLMTrain.element('model')],
                outputs=[LLMTrain.element('train_record')] + list(LLMTrain.valid_elements().values()))
            app.load(
                partial(LLMRLHF.update_input_model, arg_cls=RLHFArguments),
                inputs=[LLMRLHF.element('model')],
                outputs=[LLMRLHF.element('train_record')] + list(LLMRLHF.valid_elements().values()))
            app.load(
                partial(LLMGRPO.update_input_model, arg_cls=RLHFArguments),
                inputs=[LLMGRPO.element('model')],
                outputs=[LLMGRPO.element('train_record')] + list(LLMGRPO.valid_elements().values()))
            app.load(
                partial(LLMInfer.update_input_model, arg_cls=DeployArguments, has_record=False),
                inputs=[LLMInfer.element('model')],
                outputs=list(LLMInfer.valid_elements().values()))
            app.load(
                partial(LLMExport.update_input_model, arg_cls=ExportArguments, has_record=False),
                inputs=[LLMExport.element('model')],
                outputs=list(LLMExport.valid_elements().values()))
            app.load(
                partial(LLMEval.update_input_model, arg_cls=EvalArguments, has_record=False),
                inputs=[LLMEval.element('model')],
                outputs=list(LLMEval.valid_elements().values()))
            app.load(
                partial(LLMSample.update_input_model, arg_cls=SamplingArguments, has_record=False),
                inputs=[LLMSample.element('model')],
                outputs=list(LLMSample.valid_elements().values()))
        app.queue(**concurrent).launch(server_name=server, inbrowser=True, server_port=port, height=800, share=share)


def webui_main(args: Optional[Union[List[str], WebUIArguments]] = None):
    return SwiftWebUI(args).main()
