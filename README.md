chosen-plaintext
================

Python framework for extracting plaintext data from a block cipher in ECB or CBC mode for the specific case where a user input is encrypted directly before a secret that needs to be recovered and the ciphertext can be observed by the attacker.

Recovery is possible in the following cases:
* Any ECB mode block cipher.
* A CBC mode block cipher when the IV is static.
* A CBC mode block cipher when the IV is predictable, and the attacker has full control on the first block.

A few vulnerable samples are provided, one for each use case described above.

What does it do?
----------------

This class facilitates the exploitation of a chosen plaintext attack against a vulnerable application. This project was created during [NorthSec 2014](http://nsec.io/en/) for solving some challenges.

Limitations & Expectations
--------------------------

The algorithm implemented here makes a few assumptions that should cover most simple use cases.

* The attacker-controlled plaintext must always appear _before_ the plaintext data that will be recovered.
* It is expected that each plaintext byte maps to a single byte of encrypted data. In cases where a byte of data is encoded or escaped into multiple bytes, recovery will fail. Such cases include when `"` is escaped into `\"`, or a space character is transformed in `%20`, etc.
* In CBC mode, the `IV()` method will be called once before each call to `ciphertext()` to retreive the IV that correspond to the next ciphertext.
* In CBC mode with a predictable IV, there is an additional requirement that the first block be fully controlled by the attacker (so that the IV can be "cancelled out" from the rest of the encrypted stream). In other cases, the controlled plaintext can occur anywhere within the encrypted data.
* The block size can be automagically detected, but in the case where some data randomly change at the beginning of the encrypted stream, this auto-detection will fail.

How does it work?
-----------------

The `ChosenPlaintext` class will take care of implementing the attack, it must be extended by a base class which provides the logic for interacting with the vulnerable application. The base class need to provide at least the `ciphertext()` method and optionally the `IV()` method (only for CBC mode when the IV is not static).

Lets say we have a cryptographic system such that `e = encrypt(a | b)` where `a` is an attacker-controlled string contatenated to `b` which the attacker wishes to recover. The attacker also has a side channel that allows them to observe the encrypted blob `e`. This situation can easily occur, for instance, in a web application which encrypt some cookies containing user data.

In the simplest case, for this attack to work, the encryption function must be a block cipher where the same plaintext is always encrypted to the same ciphertext. This property is true for both ECB mode and CBC mode with a fixed IV, so both of these cases use the same algorithm to recover the plaintext.

Lets explain this by a simple example. We have an ECB mode block cipher with 8-bytes blocks, which has the following pseudocode:
```python
ciphertext = encrypt("data=%s,secret=%s" % (user_input, secret))
```
When the encryption is applied with `user_data="abcde"` and `secret="123456"`, the block layout looks like this:
```
+--------+--------+--------+
|data=abc|de,secre|t=123456|
+--------+--------+--------+
```
When we add letters to the end of `user_input`, we can observe block 1 and 2 changing but block 0 stays the same. By trying different user input length, we can determine where the user_input starts within the data stream, and the length of each block (8 byte or 16 bytes). Using this information, we can now start the attack.

We know our `user_input` starts at index 5 within the stream, so we can send a 11 times the letter `a` so that block 0 and 1 will contain `data=aaa` and `aaaaaaaa` respectively. If we send only 10 `a`'s, the block layout will look like:
```
+--------+--------+--------+--------+
|data=aaa|aaaaaaa,|secret=a|bcdef   |
+--------+--------+--------+--------+
```
with exactly one unknown letter that is concatenated at the end of our user-controlled string within block 1. This letter is part of the data we want to retreive so we can take note of the ciphertext value of block 1 at this point. Because we control block 1 entirely, it is now just a matter of guessing the correct letter at the end of our user-controlled string. We can make the data in block 1 be alternatively `aaaaaaaa`, `aaaaaaab`, ... `aaaaaaaz`, and so on. During the guessing process the block layout will alternatively look like:
```
         +--------+--------+--------+--------+
guess 0: |data=aaa|aaaaaaaa|,secret=|abcdef  |
         +--------+--------+--------+--------+
guess 1: |data=aaa|aaaaaaab|,secret=|abcdef  |
         +--------+--------+--------+--------+
guess 2: |data=aaa|aaaaaaac|,secret=|abcdef  |
         +--------+--------+--------+--------+
  ...
         +--------+--------+--------+--------+
guess n: |data=aaa|aaaaaaa,|,secret=|abcdef  |
         +--------+--------+--------+--------+
```
When we try `aaaaaaa,` as our guess, obviously we will get a match with the block 1 we noted from the previous step and we will have successfully retrieved the first letter of the data that comes directly after our `user_input`. We can then repeat the whole process by sending a 9-letter string of `a`'s so that the block layout becomes:
```
+--------+--------+--------+--------+
|data=aaa|aaaaaa,s|ecret=ab|cdef    |
+--------+--------+--------+--------+
```
We already recovered `,` so we can repeat the guessing process by making block 1 alternatively contain `aaaaaa,a`, `aaaaaa,b`, and so on until we find a match on `aaaaaa,s`.

That's all there is to do for ECB mode and CBC mode with a static IV. If the IV is not static but is predictable, the attack is still possible by XOR'ing the predicted IV with the very first block of data. This way, the resulting ciphertext data stays the requirement that "the same plaintext always encrypt to the same ciphertext" holds true.

