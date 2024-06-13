import torch
from transformers import AutoModelForCausalLM
from transformers import AutoProcessor
from PIL import Image

VISION_MODEL = "microsoft/Phi-3-vision-128k-instruct"

class Phi3V:
    def __init__(self, device):
        """ 
        Initialize Vision Model to perform OCR
        """
        self.device = device
        kwargs = {
            'trust_remote_code': True,
            'torch_dtype': torch.bfloat16 if self.device == 'cuda' and torch.cuda.get_device_capability()[0] >= 8 else 'auto',
            'device_map': self.device,
            '_attn_implementation': 'flash_attention_2' if self.device == 'cuda' else 'eager'
        }
        self.processor = AutoProcessor.from_pretrained(
            pretrained_model_name_or_path=VISION_MODEL, 
            **kwargs
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=VISION_MODEL, 
            **kwargs
        )

        messages = [
            {"role": "user", "content": "<|image_1|>\n\nYou are an expert OCR system. You are provided with images. You read text from images. You write only recognized text and nothing else. If there are more than one page you read all of them. You will be penalized for $1000000 for every word that is not in the image. Try not to write text from headers and footers. If there is no text on the image you just output 'no text'.\nWrite a text from the image\n"}, 
        ]
        self.prompt = self.processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        self.generation_args = { 
            "max_new_tokens": 1024, 
            "temperature": 0.0, 
            "do_sample": False, 
        }
    
    def recognize(self, image: Image) -> str:
        """
        Perform image recognition
        """
        inputs = self.processor(self.prompt, [image], return_tensors="pt").to(self.device)
        generate_ids = self.model.generate(
            **inputs, 
            eos_token_id=self.processor.tokenizer.eos_token_id,
            **self.generation_args,
        )
        generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]

        response = self.processor.batch_decode(
            generate_ids, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )[0]
        return response