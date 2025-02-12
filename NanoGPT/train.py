# I followed Andrej Karpathy's YT tutorial, "Let's build GPT: from scratch, in code, spelled out."
# https://youtu.be/kCc8FmEb1nY


import torch
import torch.nn as nn
from torch.nn import functional as F

with open('.\\NanoGPT\\input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

chars = sorted(list(set(text)))
vocab_size = len(chars)
encodelookup = {ch:i for i,ch in enumerate(chars)}
decodelookup = {i:ch for i,ch in enumerate(chars)}
encode = lambda s: [encodelookup[c] for c in s]
decode = lambda l: "".join([decodelookup[i] for i in l])
data = torch.tensor(encode(text), dtype = torch.long)

n = int(0.9*len(data))
train_data = data[:n]
test_data = data[n:]
device = 'cuda' if torch.cuda.is_available() else 'cpu' # I know I'll have to train on CPU
# but just pointing out the GPU training option here.
max_iters = 5000
eval_interval = 1000
learning_rate = 3e-4
eval_iters = 200
n_embd = 192
n_head = 6
dropout = 0.2
block_size = 192
batch_size = 64

def get_batch(split):
    data = train_data if split == 'train' else test_data
    ix = torch.randint(len(data)-block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    return x,y

class FeedForward(nn.Module):
    def __init__(self, n_embd):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(n_embd, 4*n_embd), 
                                 nn.ReLU(),
                                 nn.Linear(4*n_embd, n_embd),
                                 nn.Dropout(dropout))
    
    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        head_size = n_embd//n_head
        self.sa = MultiHeadAttention(n_head, head_size)
        self.ffwd = FeedForward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x

class Head(nn.Module):
    def __init__(self, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B,T,C = x.shape
        k = self.key(x)
        q = self.query(x)
        wei = q @ k.transpose(-2,-1) * C**-0.5 
        # normalize to make sure variance doesn't get too high
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        v = self.value(x)
        out = wei @ v
        return out

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        out = self.dropout(self.proj(out))
        return out

class BigramLanguageModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        
        self.blocks = nn.Sequential(
            Block(n_embd, n_head),
            Block(n_embd, n_head),
            Block(n_embd, n_head),
            Block(n_embd, n_head),
            nn.LayerNorm(n_embd),
        )

        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx, targets=None):
        B,T = idx.shape
        tok_emb = self.token_embedding_table(idx)
        pos_emb = self.position_embedding_table(torch.arange(T, device=device))
        x = tok_emb + pos_emb
        x = self.blocks(x)
        logits = self.lm_head(x)
        if targets is None:
            loss = None
        else:
            B,T,C = logits.shape
            logits = logits.view(B*T, C)
            targets = targets.view(B*T)
            loss = F.cross_entropy(logits, targets)
        return logits, loss
    
    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -block_size:]
            logits, loss = self(idx_cond)
            logits = logits[:, -1, :]
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx


model = BigramLanguageModel()
m = model.to(device)
xb, yb = get_batch('train')
logits, loss = m(xb, yb)
print(loss.item())
print(decode(m.generate(idx = torch.zeros((1,1), dtype = torch.long), max_new_tokens=100)[0].tolist()))

optimizer = torch.optim.AdamW(m.parameters(), lr = learning_rate)

for steps in range(max_iters):
    xb, yb = get_batch('train')
    logits, loss = m(xb, yb)
    if steps % eval_interval == eval_interval-1:
        print(steps, loss.item())
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

final_out = decode(m.generate(idx = torch.zeros((1,1), dtype = torch.long), max_new_tokens=10000)[0].tolist())
print(final_out)
with open(".\\NanoGPT\\output.txt", 'w') as file:
    file.write(final_out)