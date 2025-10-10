import torch
from torch.utils.data import DataLoader, Dataset
from torch import nn, optim

data = [
    ("It is flooded in my country", "Sorry about that"),
    ("It is raining today", "Hope you're safe"),
    ("I just got a new phone", "Congratulations!"),
    ("My device spoiled today", "Sorry man. Take heart"),
    ("wsp", "Hey man"),
    ("What's up", "I'm good as usual"),
    ("Lol", "Thats not very sporty of you"),
    ("I am going back to school", "Glad to hear it"),
    ("I am resuming soon", "Good luck"),
    ("Are you okay?", "Of course! Is there a reason to ask?"),
    ("You're strange", "Not really! I'm just different"),
]

def tokenize(text):
    return text.lower().split()

all_words = [txt for txt, desc in data] + [desc for txt, desc in data]
words = set(" ".join(all_words).lower().split())
w2idx = {w: i+3 for i, w in enumerate(words)}
w2idx["<PAD>"] = 0
w2idx["<SOS>"] = 1
w2idx["<EOS>"] = 2
idx2w = {i: w for w, i in w2idx.items()}
VOCAB_SIZE = len(w2idx)
EMBED_SIZE = 64
HIDDEN_SIZE = 128

def encode(text):
    tokens = tokenize(text)
    return [w2idx["<SOS>"]] + [w2idx[t] for t in tokens if t in w2idx] + [w2idx["<EOS>"]]
class MessageData(Dataset):
    def __init__(self, pair):
        self.data = [(encode(txt), encode(desc)) for txt, desc in pair]
    def __len__(self):
        return len(self.data)
    def __getitem__(self, index):
        return self.data[index]
def collate_fn(batch):
    txts, descs = zip(*batch)
    txts_padded = nn.utils.rnn.pad_sequence([torch.tensor(x) for x in txts], batch_first=True, padding_value=w2idx["<PAD>"])
    descs_padded = nn.utils.rnn.pad_sequence([torch.tensor(x) for x in descs], batch_first=True, padding_value=w2idx["<PAD>"])
    return txts_padded, descs_padded
dataset = MessageData(pair=data)
loader = DataLoader(dataset=dataset, batch_size=4, shuffle=True, collate_fn=collate_fn)

class Attention(nn.Module):
    def __init__(self, hs):
        super(Attention, self).__init__()
        self.attn = nn.Linear(hs * 2, hs)
        self.v = nn.Linear(hs, 1, bias=False)
    def forward(self, hidden, encoder_output):
        seq_len = encoder_output.size(1)
        hidden = hidden.repeat(1, seq_len, 1)
        energy = torch.tanh(self.attn(torch.cat((hidden, encoder_output), dim=2)))
        attention = self.v(energy).squeeze(2)
        return torch.softmax(attention, dim=1)
class Encoder(nn.Module):
    def __init__(self, vs, es, hs):
        super(Encoder, self).__init__()
        self.embedding = nn.Embedding(vs, es)
        self.rnn = nn.GRU(es, hs, batch_first=True)
    def forward(self, x, return_output=False):
        x = self.embedding(x)
        output, hidden = self.rnn(x)
        if return_output:
            return output, hidden
        return hidden
class Decoder(nn.Module):
    def __init__(self, vs, es, hs):
        super(Decoder, self).__init__()
        self.embedding = nn.Embedding(vs, es)
        self.attn = Attention(hs)
        self.rnn = nn.GRU(es + hs, hs, batch_first=True)
        self.fc = nn.Linear(hs, vs)
    def forward(self, x, hidden, encoder_output):
        x = self.embedding(x)
        attn_weight = self.attn(hidden.transpose(0, 1), encoder_output)
        context = torch.bmm(attn_weight.unsqueeze(1), encoder_output)
        context = context.repeat(1, x.size(1), 1)
        other_rnn = torch.cat((x, context), dim=2)
        output, hidden = self.rnn(other_rnn, hidden)
        output = self.fc(output)
        return output, hidden
class FXModel(nn.Module):
    def __init__(self, encoder, decoder):
        super(FXModel, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
    def forward(self, src, tgt):
        encoder_output, hidden = self.encoder(src, return_output=True)
        output, _ = self.decoder(tgt[:, :-1], hidden, encoder_output)
        return output

encoder = Encoder(vs=VOCAB_SIZE, es=EMBED_SIZE, hs=HIDDEN_SIZE)
decoder = Decoder(vs=VOCAB_SIZE, hs=HIDDEN_SIZE, es=EMBED_SIZE)
modelo = FXModel(encoder, decoder)

criterion = nn.CrossEntropyLoss(ignore_index=w2idx["<PAD>"])
optimizer = optim.Adam(modelo.parameters(), lr=0.001)

for epoch in range(40):
    for src, tgt in loader:
        optimizer.zero_grad()
        output = modelo(src, tgt)
        loss = criterion(output.reshape(-1, VOCAB_SIZE), tgt[:, 1:].reshape(-1))
        loss.backward()
        optimizer.step()

def generator(model, src, min_length=2, max_length=10):
    model.eval()
    encoder_output, hidden = model.encoder(src, return_output=True)
    x = torch.tensor([[w2idx["<SOS>"]]])
    results = []
    for i in range(max_length):
        output, hidden = model.decoder(x, hidden, encoder_output)
        next_token = output.argmax(2)[:, -1]
        if next_token.item() == w2idx["<EOS>"] and i >= min_length:
            break
        elif next_token.item() != w2idx["<EOS>"]:
            results.append(idx2w[next_token.item()])
        x = next_token.unsqueeze(0)
    return " ".join(results)

sample = "My area is flooded seriously"
encoded = torch.tensor([encode(sample)])
print(generator(model=modelo, src=encoded))