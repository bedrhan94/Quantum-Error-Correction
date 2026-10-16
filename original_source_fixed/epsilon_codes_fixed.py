import random


class GaussianInteger:
    def __init__(self, real, imag, modulus):
        self.real = real % modulus
        self.imag = imag % modulus
        self.q = modulus

    def __add__(self, other):
        return GaussianInteger(self.real + other.real, self.imag + other.imag, self.q)

    def __sub__(self, other):
        return GaussianInteger(self.real - other.real, self.imag - other.imag, self.q)

    def __mul__(self, other):
        real = self.real * other.real - self.imag * other.imag
        imag = self.real * other.imag + self.imag * other.real
        return GaussianInteger(real, imag, self.q)

    def conjugate(self):
        return GaussianInteger(self.real, -self.imag, self.q)

    def __eq__(self, other):
        return self.real == other.real and self.imag == other.imag

    def __hash__(self):
        return hash((self.real, self.imag))

    def __repr__(self):
        if self.imag == 0:
            return f"{self.real}"
        elif self.real == 0:
            return f"{self.imag}i"
        else:
            return f"{self.real}+{self.imag}i"

    def mannheim_weight(self):
        return min(self.real, self.q - self.real) + min(self.imag, self.q - self.imag)


class GaussianVector:
    def __init__(self, components, modulus):
        self.q = modulus
        self.n = len(components)
        self.components = []
        for c in components:
            if isinstance(c, tuple):
                self.components.append(GaussianInteger(c[0], c[1], modulus))
            else:
                self.components.append(c)

    def __add__(self, other):
        return GaussianVector(
            [self.components[i] + other.components[i] for i in range(self.n)], self.q)

    def __sub__(self, other):
        return GaussianVector(
            [self.components[i] - other.components[i] for i in range(self.n)], self.q)

    def scalar_mult(self, scalar):
        if isinstance(scalar, tuple):
            scalar = GaussianInteger(scalar[0], scalar[1], self.q)
        return GaussianVector([scalar * c for c in self.components], self.q)

    def hermitian_inner_product(self, other):
        result = GaussianInteger(0, 0, self.q)
        for i in range(self.n):
            result = result + (self.components[i] * other.components[i].conjugate())
        return result

    def __eq__(self, other):
        return all(self.components[i] == other.components[i] for i in range(self.n))

    def __hash__(self):
        return hash(tuple((c.real, c.imag) for c in self.components))

    def __repr__(self):
        return f"({', '.join(str(c) for c in self.components)})"

    def mannheim_weight(self):
        return sum(c.mannheim_weight() for c in self.components)


class GaussianCodeN:

    def __init__(self, generator, modulus, max_elements=10**7):
        self.q = modulus
        if isinstance(generator, list):
            self.generator = GaussianVector(generator, modulus)
        else:
            self.generator = generator
        self.n = self.generator.n
        self.elements = set()
        self._generate_elements(max_elements)

    def _generate_elements(self, max_elements):
        self.elements.add(GaussianVector([(0, 0)] * self.n, self.q))
        for a in range(self.q):
            for b in range(self.q):
                s = GaussianInteger(a, b, self.q)
                self.elements.add(self.generator.scalar_mult(s))
                if len(self.elements) >= max_elements:
                    return

    def size(self):
        return len(self.elements)

    def hermitian_dual(self):
        if self.n != 2:
            raise NotImplementedError("hermitian_dual yalnizca n=2 icin yazildi.")
        zero = GaussianInteger(0, 0, self.q)
        dual_elements = []
        for a1 in range(self.q):
            for b1 in range(self.q):
                for a2 in range(self.q):
                    for b2 in range(self.q):
                        candidate = GaussianVector([(a1, b1), (a2, b2)], self.q)
                        # FIX (epsilon_qec_research): test against every element of the code, not only
                        # self.generator - a dual returned by this method has generator = 0, so the
                        # original line made dual(dual(C)) equal to the whole space.
                        if all(c.hermitian_inner_product(candidate) == zero for c in self.elements):
                            dual_elements.append(candidate)
        new_code = GaussianCodeN([(0, 0), (0, 0)], self.q)
        new_code.elements = set(dual_elements)
        return new_code

    def minimum_distance(self, exclude_code=None):
        min_weight = float('inf')
        min_element = None
        for elem in self.elements:
            if all(c.real == 0 and c.imag == 0 for c in elem.components):
                continue
            if exclude_code and elem in exclude_code.elements:
                continue
            weight = elem.mannheim_weight()
            if weight < min_weight:
                min_weight = weight
                min_element = elem
        return min_weight, min_element


def find_epsilon(C2, C1):
    zero = GaussianVector([(0, 0)] * C2.n, C2.q)
    eps = [zero]
    index = C2.size() // C1.size()
    for elem in C2.elements:
        if len(eps) == index:
            break
        if elem == zero:
            continue
        if not any((elem - rep) in C1.elements for rep in eps):
            eps.append(elem)
    return eps


def find_epsilon_canonical(C2, C1, q, alpha2_tuple):
    index = C2.size() // C1.size()
    alpha2 = GaussianInteger(alpha2_tuple[0], alpha2_tuple[1], q)
    epsilon = []
    for a in range(q):
        for b in range(q):
            rep = GaussianInteger(a, b, q) * alpha2
            rep_vec = GaussianVector([(rep.real, rep.imag)], q)
            if not any((rep_vec - existing) in C1.elements for existing in epsilon):
                epsilon.append(rep_vec)
            if len(epsilon) == index:
                return epsilon
    return epsilon


def verify_epsilon(epsilon, C1, label):
    print(f"\n=== {label} ===")
    print(f"eps kumesi: {epsilon}")
    print(f"Mannheim agirliklari: {sorted(e.mannheim_weight() for e in epsilon)}")
    all_distinct = True
    for i, ei in enumerate(epsilon):
        for j, ej in enumerate(epsilon):
            if i < j and (ei - ej) in C1.elements:
                print(f"UYARI: e{i} - e{j} C1 icinde!")
                all_distinct = False
    print(f"Kosetler ayrik: {all_distinct}")
    return all_distinct


def decode(y, eps, C1):
    candidates = [rep for rep in eps if (y - rep) in C1.elements]
    if len(candidates) == 0:
        return None, None
    elif len(candidates) == 1:
        decoded_e = candidates[0]
        return decoded_e, y - decoded_e
    else:
        raise ValueError(
            f"Non-unique decoding! {len(candidates)} candidates found. eps is invalid.")


def run_simulation(q, gen_c2, gen_c1, label, trials=5000):
    C2 = GaussianCodeN(gen_c2, q)
    C1 = GaussianCodeN(gen_c1, q)
    eps = find_epsilon(C2, C1)
    c_list = list(C1.elements)

    success = 0
    unique_count = 0
    non_unique = 0

    for _ in range(trials):
        c = random.choice(c_list)
        e_true = random.choice(eps)
        y = c + e_true

        try:
            decoded_e, c_recovered = decode(y, eps, C1)
            if decoded_e is not None:
                unique_count += 1
                if c_recovered == c:
                    success += 1
        except ValueError:
            non_unique += 1

    return {
        'label': label,
        'trials': trials,
        'eps_size': len(eps),
        'C1_size': C1.size(),
        'C2_size': C2.size(),
        'success': success,
        'unique': unique_count,
        'non_unique': non_unique,
        'success_rate': success / trials,
    }


def print_results(results):
    print(f"\n{'=' * 75}")
    print(f"{'Ring':<14} {'|C1|':<8} {'|C2|':<8} {'|eps|':<6} "
          f"{'Unique':<8} {'Non-unique':<12} {'Success'}")
    print(f"{'=' * 75}")
    for r in results:
        print(f"{r['label']:<14} {r['C1_size']:<8} {r['C2_size']:<8} "
              f"{r['eps_size']:<6} {r['unique']:<8} {r['non_unique']:<12} "
              f"{r['success']}/{r['trials']} ({r['success_rate'] * 100:.1f}%)")
    print(f"{'=' * 75}")


def search_css_pairs(q, max_found=None):
    print(f"Z_{q}[i]^2 icinde CSS ciftleri taraniyor...")
    generators = [(a, b) for a in range(q) for b in range(q) if (a, b) != (0, 0)]
    found = []

    for g2a in generators:
        for g2b in generators:
            C2 = GaussianCodeN([g2a, g2b], q)
            size2 = C2.size()
            C2_perp = None

            for g1a in generators:
                for g1b in generators:
                    C1 = GaussianCodeN([g1a, g1b], q)

                    if C1.size() >= size2:
                        continue
                    if not all(e in C2.elements for e in C1.elements):
                        continue

                    if C2_perp is None:
                        C2_perp = C2.hermitian_dual()
                    if C2_perp.size() >= C1.size():
                        continue
                    if all(e in C1.elements for e in C2_perp.elements):
                        K = C1.size() // C2_perp.size()
                        if K > 1:
                            print(f"C2=<{g2a},{g2b}>, C1=<{g1a},{g1b}>, "
                                  f"|C2|={size2}, |C1|={C1.size()}, "
                                  f"|C2_perp|={C2_perp.size()}, K={K}")
                            found.append((g2a, g2b, g1a, g1b, K))
                            if max_found and len(found) >= max_found:
                                return found

    if not found:
        print("Gecerli CSS ornegi bulunamadi.")
    else:
        print(f"\nToplam: {len(found)}")
    return found


if __name__ == "__main__":
    examples = [
        (25,  [(2, 1)], [(3, 4)], (2, 1), "Z_25[i]"),
        (85,  [(2, 1)], [(7, 6)], (2, 1), "Z_85[i]"),
        (325, [(3, 2)], [(4, 7)], (3, 2), "Z_325[i]"),
    ]

    for q, g2, g1, alpha2, label in examples:
        C2 = GaussianCodeN(g2, q)
        C1 = GaussianCodeN(g1, q)
        nested = all(e in C2.elements for e in C1.elements)
        print(f"\n{label}: |C2|={C2.size()}, |C1|={C1.size()}, C1<=C2: {nested}")
        eps = find_epsilon_canonical(C2, C1, q, alpha2)
        verify_epsilon(eps, C1, label)

    results = [run_simulation(q, g2, g1, label) for q, g2, g1, _, label in examples]
    print_results(results)
