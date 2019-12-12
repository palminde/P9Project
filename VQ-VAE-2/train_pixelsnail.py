import argparse
import numpy as np
import tensorflow as tf


try:
    from apex import amp

except ImportError:
    amp = None

import Utils.DataHandler
from PixelSNAIL import PixelSNAIL
from scheduler import CycleScheduler


def train(args, epoch, loader, model, optimizer, scheduler):

    criterion = nn.CrossEntropyLoss()

    for i, (top, bottom, label) in enumerate(loader):
        model.zero_grad()

        top = top.to(device)

        if args.hier == 'top':
            target = top
            out, _ = model(top)

        elif args.hier == 'bottom':
            bottom = bottom.to(device)
            target = bottom
            out, _ = model(bottom, condition=top)

        loss = criterion(out, target)
        loss.backward()

        if scheduler is not None:
            scheduler.step()
        optimizer.step()

        _, pred = out.max(1)
        correct = (pred == target).float()
        accuracy = correct.sum() / target.numel()

        lr = optimizer.param_groups[0]['lr']

        loader.set_description(
            (
                f'epoch: {epoch + 1}; loss: {loss.item():.5f}; '
                f'acc: {accuracy:.5f}; lr: {lr:.5f}'
            )
        )


class PixelTransform:
    def __init__(self):
        pass

    def __call__(self, input):
        ar = np.array(input)

        return torch.from_numpy(ar).long()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--epoch', type=int, default=420)
    parser.add_argument('--hier', type=str, default='top')
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--channel', type=int, default=256)
    parser.add_argument('--n_res_block', type=int, default=4)
    parser.add_argument('--n_res_channel', type=int, default=256)
    parser.add_argument('--n_out_res_block', type=int, default=0)
    parser.add_argument('--n_cond_res_block', type=int, default=3)
    parser.add_argument('--dropout', type=float, default=0.1)
    parser.add_argument('--amp', type=str, default='O0')
    parser.add_argument('--sched', type=str)
    parser.add_argument('--ckpt', type=str)
    parser.add_agument('--img_size', type=int, help='Image size as int')
    parser.add_argument('path', type=str)

    args = parser.parse_args()

    print(args)

    dataset = LMDBDataset(args.path)
    loader = DataLoader(
        dataset, batch_size=args.batch, shuffle=True, num_workers=4, drop_last=True
    )

    ckpt = {}

    if args.ckpt is not None:
        ckpt = tf.saved_model.load(args.ckpt)
        args = ckpt['args']

    top_input = 0
    bottom_input = 0
    if args.img_size == 32:
        top_input = 4
        bottom_input = 8
    elif args.img_size == 256:
        top_input = 32
        bottom_input = 64
    else:
        raise('Unsupported image size')

    if args.hier == 'top':
        model = PixelSNAIL(
            [top_input, top_input],
            512,
            args.channel,
            5,
            4,
            args.n_res_block,
            args.n_res_channel,
            dropout=args.dropout,
            n_out_res_block=args.n_out_res_block,
        )

    elif args.hier == 'bottom':
        model = PixelSNAIL(
            [bottom_input, bottom_input],
            512,
            args.channel,
            5,
            4,
            args.n_res_block,
            args.n_res_channel,
            attention=False,
            dropout=args.dropout,
            n_cond_res_block=args.n_cond_res_block,
            cond_res_channel=args.n_res_channel,
        )

    if 'model' in ckpt:
        model.load_state_dict(ckpt['model'])


    optimizer = tf.keras.optimizers.Adam(model.parameters(), lr=args.lr)

    if amp is not None:
        model, optimizer = amp.initialize(model, optimizer, opt_level=args.amp)

    #model = nn.DataParallel(model)
    #model = model.to(device)

    scheduler = None
    if args.sched == 'cycle':
        scheduler = CycleScheduler(
            optimizer, args.lr, n_iter=len(loader) * args.epoch, momentum=None
        )

    for i in range(args.epoch):
        train(args, i, loader, model, optimizer, scheduler, device)
        torch.save(
            {'model': model.module.state_dict(), 'args': args},
            f'checkpoint/pixelsnail_{args.hier}_{str(i + 1).zfill(3)}.pt',
        )
