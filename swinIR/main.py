import os
import sys
sys.path.append("./swinIR/")

import torch
import torchvision.transforms as transforms

from packages.swinIR.network import SwinIR
from packages.utils.util import convert_img_type
from packages.utils.model_util import download_weight

SRnet = SwinIR(upscale=4, in_chans=3, img_size=64, window_size=8,
                        img_range=1., depths=[6, 6, 6, 6, 6, 6, 6, 6, 6], embed_dim=240,
                        num_heads=[8, 8, 8, 8, 8, 8, 8, 8, 8],
                        mlp_ratio=2, upsampler='nearest+conv', resi_connection='3conv')
file_PATH="./packages/swinIR/ptnn/swinIR.pth"
if not os.path.isfile(file_PATH):
    download_weight('swinIR')

SRnet.load_state_dict(torch.load(file_PATH)['params_ema'], strict=True)
SRnet.to("cuda").eval()

def do_SR(pil_image):
    pil_image = convert_img_type(pil_image, 'pil')
    with torch.no_grad():

        img_lq = transforms.ToTensor()(pil_image).unsqueeze(0).to("cuda")
        scale = 4
        _, _, h_old, w_old = img_lq.size()
        h_pad = (h_old // 8 + 1) * 8 - h_old
        w_pad = (w_old // 8 + 1) * 8 - w_old
        img_lq = torch.cat([img_lq, torch.flip(img_lq, [2])], 2)[:, :, :h_old + h_pad, :]
        img_lq = torch.cat([img_lq, torch.flip(img_lq, [3])], 3)[:, :, :, :w_old + w_pad]
        output = SRnet(img_lq)
        output = output[..., :h_old * scale, :w_old * scale]

        return (output.permute(0, 2, 3, 1) * 255).clamp(0, 255).squeeze().detach().cpu().numpy()
            
