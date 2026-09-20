import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.security import get_password_hash
from app.models.user import User
from app.models.academic import Course, Unit, CourseOutcome
from app.models.resource import Resource, ResourceChunk
from app.services.rag.vector_store import vector_store

SAMPLE_COURSES = [
    {
        "code": "CS301",
        "name": "Data Structures & Algorithms",
        "department": "Computer Science & Engineering",
        "semester": "Semester III",
        "academic_year": "2025-2026",
        "description": "Comprehensive study of abstract data types, trees, graph algorithms, dynamic programming, and complexity analysis.",
        "units": [
            {"unit_number": 1, "title": "Linear Data Structures & Analysis", "topics": "Asymptotic Notations (Big-O, Omega, Theta), Arrays, Linked Lists (Singly, Doubly, Circular), Stacks, Queues, Deque, Infix to Postfix conversion."},
            {"unit_number": 2, "title": "Trees & Self-Balancing Trees", "topics": "Binary Trees, Binary Search Trees (BST), AVL Trees (Rotations and Balance Factor), Red-Black Trees, B-Trees, B+ Trees, Tree Traversals (Inorder, Preorder, Postorder)."},
            {"unit_number": 3, "title": "Priority Queues & Disjoint Sets", "topics": "Binary Heaps (Min-Heap, Max-Heap), Heap Sort, Fibonacci Heaps, Disjoint Set Union (DSU), Path Compression, Union by Rank."},
            {"unit_number": 4, "title": "Graph Algorithms", "topics": "Graph Representation (Adjacency Matrix & List), BFS, DFS, Topological Sorting, Minimum Spanning Trees (Kruskal, Prim), Shortest Paths (Dijkstra, Bellman-Ford, Floyd-Warshall)."},
            {"unit_number": 5, "title": "Algorithm Design Techniques & Complexity", "topics": "Divide and Conquer (Merge Sort, Quick Sort), Greedy Algorithms (Huffman Coding, Fractional Knapsack), Dynamic Programming (0/1 Knapsack, LCS, Matrix Chain Multiplication), Backtracking (N-Queens), NP-Completeness, P vs NP."}
        ],
        "cos": [
            {"code": "CO1", "description": "Analyze asymptotic time and space complexity of linear and non-linear algorithms.", "target_bloom_level": "Analyze"},
            {"code": "CO2", "description": "Implement and balance advanced hierarchical tree structures for efficient searching.", "target_bloom_level": "Apply"},
            {"code": "CO3", "description": "Design optimal graph algorithms for network routing and spanning tree construction.", "target_bloom_level": "Create"},
            {"code": "CO4", "description": "Formulate dynamic programming and greedy strategies for complex optimization problems.", "target_bloom_level": "Evaluate"},
            {"code": "CO5", "description": "Assess computational tractability and classify problems into P, NP, and NP-Complete classes.", "target_bloom_level": "Evaluate"}
        ]
    },
    {
        "code": "CS401",
        "name": "Database Management Systems",
        "department": "Computer Science & Engineering",
        "semester": "Semester IV",
        "academic_year": "2025-2026",
        "description": "Relational data model, relational algebra, SQL, database normalization, indexing, transaction processing, and concurrency control.",
        "units": [
            {"unit_number": 1, "title": "Database Architecture & ER Modeling", "topics": "Three-Schema Architecture, Data Independence, Relational Data Model, ER Diagrams, Extended ER Features, Keys (Primary, Foreign, Candidate, Super Key)."},
            {"unit_number": 2, "title": "Relational Algebra & Advanced SQL", "topics": "Relational Algebra Operations (Select, Project, Cartesian Product, Joins, Division), SQL Queries, Nested Subqueries, Aggregations, Group By, Having, Views, Triggers."},
            {"unit_number": 3, "title": "Schema Refinement & Normalization", "topics": "Functional Dependencies, Armstrong Axioms, Normal Forms (1NF, 2NF, 3NF, BCNF, 4NF, 5NF), Lossless Join Decomposition, Dependency Preservation."},
            {"unit_number": 4, "title": "Storage & Indexing", "topics": "File Organization, RAID Levels, Hash-based Indexing, Tree-based Indexing (B+ Tree Indexing), Clustered vs Non-clustered Indexes, Query Cost Estimation."},
            {"unit_number": 5, "title": "Transactions & Concurrency Control", "topics": "ACID Properties, Serializability (Conflict & View), Recoverability, Lock-Based Protocols (2PL, Strict 2PL), Deadlock Detection and Prevention, Timestamp Ordering, Write-Ahead Logging (WAL)."}
        ],
        "cos": [
            {"code": "CO1", "description": "Construct conceptual ER models and map them to normalized relational schemas.", "target_bloom_level": "Apply"},
            {"code": "CO2", "description": "Formulate complex SQL queries and relational algebra expressions for data retrieval.", "target_bloom_level": "Apply"},
            {"code": "CO3", "description": "Analyze functional dependencies to decompose relational schemas into BCNF/3NF.", "target_bloom_level": "Analyze"},
            {"code": "CO4", "description": "Evaluate indexing techniques and calculate query execution costs.", "target_bloom_level": "Evaluate"},
            {"code": "CO5", "description": "Design transaction schedules that ensure strict ACID guarantees and prevent deadlocks.", "target_bloom_level": "Create"}
        ]
    },
    {
        "code": "IT701PC",
        "name": "Information Security",
        "department": "Information Technology",
        "semester": "IV Year I Semester",
        "academic_year": "2025-2026",
        "description": "Comprehensive study of security attacks, services, classical and modern cryptography, DES, Blowfish, RSA, Diffie-Hellman, ECC, digital signatures, hash functions, IP security, web security (SSL/TLS/SET), firewalls, and intrusion detection systems.",
        "units": [
            {
                "unit_number": 1,
                "title": "Security Attacks, Services, Mechanisms & Classical Encryption Techniques",
                "topics": "Security Attacks: Interruption, Interception, Modification and Fabrication. Security Services: Confidentiality, Authentication, Integrity, Non-repudiation, Access Control and Availability. Mechanisms: A model for Internet work security. Classical Encryption Techniques: DES, Strength of DES, Differential and Linear Cryptanalysis, Block Cipher Design Principles and Modes of Operation, Blowfish, Placement of Encryption Function, Traffic Confidentiality, Key Distribution, Random Number Generation."
            },
            {
                "unit_number": 2,
                "title": "Public Key Cryptography, Message Authentication & Hash Functions",
                "topics": "Public Key Cryptography Principles, RSA algorithm, Key Management, Diffie-Hellman Key Exchange, Elliptic Curve Cryptography. Message Authentication and Hash Functions: Authentication Requirements and Functions, Message Authentication, Hash Functions, MACs, SHA-512, HMAC."
            },
            {
                "unit_number": 3,
                "title": "Digital Signatures, Authentication Protocols & Email Security",
                "topics": "Digital Signatures: Authentication Protocols, Digital Signature Standard (DSS). Authentication Applications: Kerberos, X.509 Directory Authentication Service. Email Security: Pretty Good Privacy (PGP) and S/MIME."
            },
            {
                "unit_number": 4,
                "title": "IP Security Architecture & Web Security",
                "topics": "IP Security: Overview, IP Security Architecture, Authentication Header (AH), Encapsulating Security Payload (ESP), Combining Security Associations and Key Management. Web Security: Web Security Requirements, Secure Socket Layer (SSL), Transport Layer Security (TLS), Secure Electronic Transaction (SET)."
            },
            {
                "unit_number": 5,
                "title": "Intruders, Viruses, Firewalls & Intrusion Detection Systems",
                "topics": "Intruders, Viruses and related threats, Firewalls, Firewall Design Principles, Trusted Systems, Intrusion Detection Systems (IDS)."
            }
        ],
        "cos": [
            {
                "code": "CO1",
                "description": "Demonstrate the knowledge of cryptography, network security concepts and applications.",
                "target_bloom_level": "Understand"
            },
            {
                "code": "CO2",
                "description": "Ability to apply security principles in system design.",
                "target_bloom_level": "Apply"
            },
            {
                "code": "CO3",
                "description": "Ability to identify and investigate vulnerabilities and security threats and mechanisms to counter them.",
                "target_bloom_level": "Analyze"
            }
        ]
    }
]

SAMPLE_RESOURCES = [
    {
        "course_code": "CS301",
        "title": "Data Structures Comprehensive Academic Text & Notes",
        "file_name": "CS301_DSA_University_Textbook.pdf",
        "file_type": "pdf",
        "document_type": "textbook",
        "chunks": [
            {
                "unit": 1,
                "topic": "Asymptotic Complexity & Linked Lists",
                "content": "Asymptotic analysis evaluates algorithmic efficiency independent of machine hardware. Big-O notation represents an upper bound on worst-case execution time, while Omega defines the lower bound and Theta denotes tight bounds. Singly linked lists provide O(1) insertion at head and O(n) traversal. Doubly linked lists maintain prev and next pointers, enabling bidirectional traversal at the cost of additional memory pointer overhead."
            },
            {
                "unit": 2,
                "topic": "AVL Trees & Balance Factors",
                "content": "An AVL tree is a self-balancing binary search tree where the difference between heights of left and right subtrees for any node (balance factor) cannot exceed +/- 1. When an insertion causes an imbalance, one of four rotations is applied: Left-Left (Single Right Rotation), Right-Right (Single Left Rotation), Left-Right (Double Rotation: Left then Right), and Right-Left (Double Rotation: Right then Left). Searching, insertion, and deletion all maintain strict O(log n) worst-case time complexity."
            },
            {
                "unit": 2,
                "topic": "B-Trees and Multi-way Search Trees",
                "content": "A B-tree of order m is a balanced search tree designed for disk storage systems. Every internal node except root has at least ceil(m/2) children and at most m children. Keys inside each node act as separation boundaries for subtrees. B+ trees store all actual records exclusively in leaf nodes linked as a doubly linked list, enabling highly efficient range queries and sequential block reads."
            },
            {
                "unit": 3,
                "topic": "Binary Heaps & Disjoint Set Union",
                "content": "A Binary Heap is a complete binary tree satisfying the heap property: in a max-heap, parent keys are greater than or equal to child keys. Array representation indexes children at 2i+1 and 2i+2. Heapify operation runs in O(n) for bottom-up construction. Disjoint Set Union (DSU) utilizes union by rank and path compression to achieve nearly O(1) amortized time per operation using the Inverse Ackermann function."
            },
            {
                "unit": 4,
                "topic": "Dijkstra and Minimum Spanning Trees",
                "content": "Dijkstra's algorithm determines the shortest path from a single source node to all other vertices in a weighted graph with non-negative edge weights using a greedy relaxation strategy and min-priority queue with time complexity O((V+E) log V). Kruskal's algorithm constructs a Minimum Spanning Tree (MST) by sorting edges and avoiding cycles via DSU, running in O(E log E)."
            },
            {
                "unit": 5,
                "topic": "Dynamic Programming & 0/1 Knapsack",
                "content": "Dynamic programming solves optimization problems possessing optimal substructure and overlapping subproblems. In the 0/1 Knapsack problem with capacity W and n items, the recurrence DP[i][w] = max(DP[i-1][w], DP[i-1][w-wt[i]] + val[i]) achieves pseudo-polynomial time complexity O(n*W). This is distinguished from fractional knapsack which allows greedy selection."
            }
        ]
    },
    {
        "course_code": "CS401",
        "title": "Database Systems Concepts & Query Optimization",
        "file_name": "CS401_DBMS_Standard_Text.pdf",
        "file_type": "pdf",
        "document_type": "textbook",
        "chunks": [
            {
                "unit": 1,
                "topic": "ER Modeling & Key Constraints",
                "content": "Entity-Relationship (ER) modeling captures real-world enterprise semantics using entity sets, attributes, and relationship sets. A primary key uniquely identifies each tuple in a relation without null attributes. Foreign keys establish referential integrity constraints between dependent and referenced tables. Cardinality constraints specify one-to-one, one-to-many, or many-to-many relationships."
            },
            {
                "unit": 3,
                "topic": "Functional Dependencies & BCNF Normalization",
                "content": "A relation R is in Boyce-Codd Normal Form (BCNF) if for every non-trivial functional dependency X -> Y, X is a superkey of R. BCNF eliminates all redundancy based on functional dependencies. A relation is in Third Normal Form (3NF) if for every X -> Y, either X is a superkey or Y is a prime attribute. 3NF guarantees dependency preservation, whereas BCNF may occasionally sacrifice dependency preservation."
            },
            {
                "unit": 5,
                "topic": "ACID Properties & Two-Phase Locking (2PL)",
                "content": "Database transactions must satisfy Atomicity, Consistency, Isolation, and Durability (ACID). Concurrency control ensures serializability under concurrent execution. Strict Two-Phase Locking (Strict 2PL) mandates that all exclusive locks acquired during the growing phase are held until transaction commit/abort, completely eliminating cascading aborts and ensuring conflict serializability."
            }
        ]
    },
    {
        "course_code": "IT701PC",
        "title": "JNTUH R22 Information Security Official Syllabus",
        "file_name": "IT701PC_Information_Security_Syllabus.pdf",
        "file_type": "pdf",
        "document_type": "syllabus",
        "chunks": [
            {
                "unit": 1,
                "topic": "Security Attacks, Services, Mechanisms & Classical Ciphers",
                "content": "Course: IT701PC Information Security (IV Year I Semester).\nUNIT I: Security Attacks: Interruption (availability attack), Interception (confidentiality attack), Modification (integrity attack), and Fabrication (authenticity attack). Security Services: Confidentiality, Authentication, Integrity, Non-repudiation, Access Control, Availability. Security Mechanisms: Encipherment, Digital Signatures, Access Control Mechanisms, Data Integrity, Authentication Exchange, Traffic Padding, Routing Control, Notarization. Model for Network Security: Sender, Receiver, Trusted Third Party, Secure Channel. Classical Encryption Techniques: Symmetric Cipher Model, Substitution Ciphers (Caesar Cipher, Playfair, Hill Cipher), Transposition Ciphers, Rotor Machines, Steganography. Data Encryption Standard (DES): Feistel Cipher Structure, 56-bit Key, 16 Rounds of Substitution and Permutation, S-Box Design, Avalanche Effect. Differential and Linear Cryptanalysis. Block Cipher Modes of Operation: Electronic Codebook (ECB), Cipher Block Chaining (CBC), Cipher Feedback (CFB), Output Feedback (OFB), Counter (CTR) mode. Blowfish Cipher: Fast Feistel cipher with 64-bit block size and variable key length (32 to 448 bits), Key-dependent S-boxes. Key Distribution and Random Number Generation."
            },
            {
                "unit": 2,
                "topic": "Public Key Cryptography, RSA, Diffie-Hellman & Hash Functions",
                "content": "UNIT II: Public Key Cryptography Principles: Asymmetric cryptography using public and private key pairs. Mathematical foundations: Prime Numbers, Fermat's and Euler's Theorems, Modular Arithmetic. RSA Algorithm: Key generation using large primes p and q, modulus n = p*q, totient phi(n) = (p-1)*(q-1), public exponent e such that gcd(e, phi(n)) = 1, private key d = e^(-1) mod phi(n). Encryption: C = M^e mod n; Decryption: M = C^d mod n. Security of RSA: Factoring problem, chosen ciphertext attacks, optimal asymmetric encryption padding (OAEP). Key Management: Distribution of Public Keys (Public Announcements, Publicly Available Directory, Public Key Authority, Public Key Certificates). Diffie-Hellman Key Exchange: Discrete Logarithm problem, shared secret computation, Man-in-the-Middle vulnerability and prevention. Elliptic Curve Cryptography (ECC): Elliptic curve arithmetic over Galois Fields GF(p) and GF(2^m), Elliptic Curve Diffie-Hellman (ECDH), ECDSA. Message Authentication and Hash Functions: Authentication Requirements and Functions, Message Authentication Codes (MAC), HMAC construction (HMAC = H((K+ XOR opad) || H((K+ XOR ipad) || M))), Secure Hash Algorithm (SHA-512) structure, 512-bit message digest, 80 rounds of processing, padding to 1024-bit blocks."
            },
            {
                "unit": 3,
                "topic": "Digital Signatures, Kerberos & X.509 PKI",
                "content": "UNIT III: Digital Signatures: Authentication Protocols, Digital Signature Properties (Authentic, Unforgeable, Non-repudiable). Digital Signature Standard (DSS): Digital Signature Algorithm (DSA) based on discrete logarithms. Authentication Applications: Kerberos Authentication Service: Kerberos Realm, Key Distribution Center (KDC), Authentication Server (AS), Ticket Granting Server (TGS), Ticket Granting Ticket (TGT), Service Tickets, Kerberos Version 4 vs Version 5 dialogue flow and timestamps. X.509 Directory Authentication Service: X.509 Certificate Structure (Version, Serial Number, Signature Algorithm, Issuer, Validity Period, Subject Name, Subject Public Key Info, Extensions), Certificate Authorities (CAs), Public Key Infrastructure (PKI) Hierarchies, Certificate Revocation Lists (CRL). Electronic Mail Security: Pretty Good Privacy (PGP): Confidentiality (CAST-128/IDEA/RSA/ElGamal), Authentication (SHA-1/RSA/DSS), Compression (ZIP), Email Compatibility (Radix-64 conversion), Key Rings (Public Key Ring and Private Key Ring). S/MIME: Secure/Multipurpose Internet Mail Extensions, Cryptographic algorithms, S/MIME certificate management, MIME content types (envelopedData, signedData, clear-signedData)."
            },
            {
                "unit": 4,
                "topic": "IP Security (IPsec) & Web Security (SSL/TLS/SET)",
                "content": "UNIT IV: IP Security: Overview of IPsec, Benefits of IPsec at the Network Layer, IPsec Applications. IP Security Architecture: Security Associations (SA), Security Parameter Index (SPI), Sequence Number Counter, Anti-Replay Window, IPsec Modes (Transport Mode vs Tunnel Mode). Authentication Header (AH): Provides data integrity and authentication of IP packets, mutable vs immutable IPv4/IPv6 header fields. Encapsulating Security Payload (ESP): Provides confidentiality, authentication, and anti-replay protection. Combining Security Associations: Basic combinations, Transport Adjacency, Iterated Tunnels. Key Management: Internet Key Exchange (IKE), Oakley Key Determination Protocol, ISAKMP (Internet Security Association and Key Management Protocol). Web Security Requirements: Web traffic threats and countermeasures at Network, Transport, and Application layers. Secure Sockets Layer (SSL) and Transport Layer Security (TLS): SSL/TLS Architecture, SSL Record Protocol (confidentiality via symmetric encryption, integrity via HMAC), SSL Handshake Protocol (Phase 1 Establish Security Capabilities, Phase 2 Server Authentication and Key Exchange, Phase 3 Client Authentication and Key Exchange, Phase 4 Finish), Change Cipher Spec Protocol, Alert Protocol. Secure Electronic Transaction (SET): SET overview, Dual Signature concept (linking order information with payment instructions without exposing credit card details to merchant), Cardholder, Merchant, Payment Gateway, Certificate Authority interactions."
            },
            {
                "unit": 5,
                "topic": "Intruders, Viruses, Firewalls & Intrusion Detection Systems",
                "content": "UNIT V: Intruders: Intruder Classes (Masquerader, Misfeasor, Clandestine User), Password Management, Password Selection Strategies, Salted Passwords, One-Time Passwords. Intrusion Detection Systems (IDS): Statistical Anomaly Detection (Threshold detection, Profile-based), Rule-Based Intrusion Detection (Rule-based anomaly detection, Rule-based penetration identification), Host-based IDS vs Network-based IDS (NIDS), Honeypots. Malicious Software (Malware): Viruses (Virus Nature, Virus Phases: Dormant, Propagation, Triggering, Execution, Virus Types: Boot Sector, File Infector, Macro, Polymorphic, Metamorphic), Worms (Worm replication, Morris Worm, Code Red, Nimda), Trojan Horses, Spyware, Ransomware, Distributed Denial of Service (DDoS) Attacks (SYN Flood, Smurf Attack, Botnets). Antivirus Approaches: Signature-based scanning, Heuristic scanning, Activity monitoring. Firewalls: Firewall Characteristics and Capabilities, Firewall Limitations. Firewall Types: Packet Filtering Router (Stateless IP/Port filtering), Stateful Inspection Firewall (State table tracking TCP 3-way handshake), Application-Level Gateway (Proxy Server), Circuit-Level Gateway. Firewall Configurations: Screened Host Firewall (Single-homed and Dual-homed bastion host), Screened Subnet Firewall (Demilitarized Zone - DMZ). Trusted Systems: Data Access Control, Mandatory Access Control (MAC) vs Discretionary Access Control (DAC), Bell-LaPadula Confidentiality Model (No Read Up, No Write Down), Biba Integrity Model, Reference Monitor, Security Kernel, Common Criteria for Information Technology Security Evaluation."
            }
        ]
    },
    {
        "course_code": "IT701PC",
        "title": "Information Security Principles & Cryptographic Engineering Textbook",
        "file_name": "IT701PC_Network_Security_Textbook.pdf",
        "file_type": "pdf",
        "document_type": "textbook",
        "chunks": [
            {
                "unit": 1,
                "topic": "DES Architecture and Cryptanalysis",
                "content": "Data Encryption Standard (DES) is a symmetric block cipher that processes 64-bit plaintext blocks into 64-bit ciphertext blocks using a 56-bit key. The algorithm comprises 16 Feistel rounds preceded by an Initial Permutation (IP) and concluded by an Inverse Initial Permutation (IP^-1). In each round, the 32-bit right half is expanded to 48 bits using the Expansion Permutation (E-box), XORed with the 48-bit subkey K_i, transformed through 8 distinct non-linear S-boxes (each mapping 6 input bits to 4 output bits), and permuted via the P-box before being XORed with the left half. Differential cryptanalysis analyzes output differences corresponding to chosen input differences, requiring 2^47 chosen plaintexts for full 16-round DES. Linear cryptanalysis constructs linear approximations of S-box operations, requiring 2^43 known plaintexts."
            },
            {
                "unit": 2,
                "topic": "RSA Mathematical Proof and Diffie-Hellman Exchange",
                "content": "The RSA algorithm relies on the intractability of the integer factorization problem. Given two distinct prime numbers p and q, calculate modulus n = p*q and Euler's Totient phi(n) = (p-1)*(q-1). Select an integer e coprime to phi(n) such that 1 < e < phi(n) and gcd(e, phi(n)) = 1. Compute private key d such that d * e = 1 (mod phi(n)), derived via the Extended Euclidean Algorithm. Encryption computes C = M^e mod n. Decryption computes M = C^d mod n = (M^e)^d mod n = M^(k*phi(n) + 1) mod n = M mod n by Euler's Totient Theorem. The Diffie-Hellman key exchange enables two parties over an insecure channel to establish a shared secret: Alice picks private a and sends A = g^a mod p; Bob picks private b and sends B = g^b mod p. Both compute K = B^a mod p = A^b mod p = g^(ab) mod p."
            },
            {
                "unit": 3,
                "topic": "Kerberos v5 Authentication and X.509 Public Key Certificates",
                "content": "Kerberos Version 5 provides trusted third-party centralized authentication in distributed networks. When client C logs in, it requests a Ticket Granting Ticket (TGT) from the Authentication Server (AS). AS returns TGT encrypted with TGS secret key and a session key K_C,TGS encrypted with client's master key. To access an application server V, client sends TGT and an Authenticator (timestamped and encrypted with K_C,TGS) to the Ticket Granting Server (TGS). TGS verifies the timestamp, generates a server ticket Ticket_V (encrypted with server's secret key K_V), and returns Ticket_V and service session key K_C,V. Client presents Ticket_V and Authenticator_V to application server V. X.509 defines digital public key certificates binding a subject identity to a public key signed by a trusted Certification Authority (CA)."
            },
            {
                "unit": 4,
                "topic": "IPsec Architecture (AH vs ESP) and SSL/TLS Handshake",
                "content": "IPsec provides network layer security protocols. Authentication Header (AH, IP protocol 51) guarantees integrity and origin authentication for the entire IP packet (including immutable IP header fields) using HMAC-SHA1 or HMAC-MD5, but provides no confidentiality. Encapsulating Security Payload (ESP, IP protocol 50) encrypts the transport payload and optionally provides authentication, inserting an ESP header before the payload and an ESP trailer after it. In Transport Mode, only the payload (e.g. TCP segment) is protected. In Tunnel Mode, the entire original IP packet is encrypted and encapsulated within a new IP header, ideal for VPN gateways. SSL/TLS Handshake Protocol negotiates cipher suites, authenticates server (and optionally client) via X.509 certificates, and establishes premaster secret to derive symmetric encryption and MAC keys."
            },
            {
                "unit": 5,
                "topic": "Firewall Architectures (DMZ) and Intrusion Detection Systems",
                "content": "A Screened Subnet Firewall creates a Demilitarized Zone (DMZ) between external untrusted networks and internal secure enterprise networks. An external packet filtering router directs public traffic (HTTP, SMTP, DNS) exclusively to bastion hosts in the DMZ. An internal packet filtering router isolates internal corporate clients from DMZ servers, ensuring that an intrusion into a DMZ web server cannot directly compromise internal databases. Intrusion Detection Systems (IDS) inspect network packets and system call traces. Statistical anomaly detection computes statistical profiles (mean, standard deviation) of normal user activity and flags statistical deviations beyond thresholds. Rule-based detection utilizes expert system rule bases to match attack signatures such as buffer overflows and port scans."
            }
        ]
    },
    {
        "course_code": "IT701PC",
        "title": "University End-Semester Information Security Past Question Paper",
        "file_name": "IT701PC_Past_Question_Paper_2024.pdf",
        "file_type": "pdf",
        "document_type": "previous_paper",
        "chunks": [
            {
                "unit": 1,
                "topic": "Security Attacks & DES Operations",
                "content": "Past Examination Reference - IT701PC Information Security.\nSection A Short Questions:\n1. Define active and passive security attacks with two concrete examples. [Unit 1, CO1, Bloom: Remember]\n2. Explain the significance of Avalanche Effect in Block Cipher Design. [Unit 1, CO1, Bloom: Understand]\nSection B Descriptive Questions:\n3. (a) Discuss the Feistel cipher design structure in DES. (b) Explain the difference between linear and differential cryptanalysis with respect to DES S-box vulnerabilities. [Unit 1, CO1/CO3, Bloom: Analyze, 10 Marks]"
            },
            {
                "unit": 2,
                "topic": "RSA and Hash Algorithm Implementations",
                "content": "Past Examination Reference - IT701PC Information Security.\nSection A Short Questions:\n4. State the mathematical condition for key generation in RSA. [Unit 2, CO1, Bloom: Remember]\n5. Differentiate between MAC and Hash function. [Unit 2, CO1, Bloom: Understand]\nSection B Descriptive Questions:\n6. In an RSA cryptosystem, user A publishes public key e = 7, n = 33. Compute private key d and encrypt message M = 2. [Unit 2, CO2, Bloom: Apply, 10 Marks]\n7. (a) Explain the structure of SHA-512 compression function. (b) Describe the Diffie-Hellman key exchange algorithm and show how the Man-in-the-Middle attack is executed. [Unit 2, CO2/CO3, Bloom: Analyze, 10 Marks]"
            },
            {
                "unit": 4,
                "topic": "IPsec Modes and SSL Protocol Verification",
                "content": "Past Examination Reference - IT701PC Information Security.\nSection A Short Questions:\n8. Distinguish between Transport Mode and Tunnel Mode in IPsec. [Unit 4, CO2, Bloom: Understand]\n9. What is the role of Dual Signature in Secure Electronic Transaction (SET)? [Unit 4, CO2, Bloom: Remember]\nSection B Descriptive Questions:\n10. (a) Explain the architecture of IPsec showing the header formats of AH and ESP. (b) Describe all phases of the SSL Handshake Protocol with a neat sequence diagram. [Unit 4, CO2, Bloom: Apply/Analyze, 10 Marks]"
            },
            {
                "unit": 5,
                "topic": "Firewall Design Principles & Intruder Detection",
                "content": "Past Examination Reference - IT701PC Information Security.\nSection A Short Questions:\n11. List four distinct types of firewalls and state their operational layer. [Unit 5, CO3, Bloom: Remember]\n12. Explain the concept of Honeypots in network defense. [Unit 5, CO3, Bloom: Understand]\nSection B Descriptive Questions:\n13. (a) Compare and contrast Statistical Anomaly Detection and Rule-Based Intrusion Detection. (b) Design a Screened Subnet Firewall architecture with DMZ for an enterprise banking portal. [Unit 5, CO3, Bloom: Evaluate/Create, 10 Marks]"
            }
        ]
    }
]

async def seed_database(db: AsyncSession):
    # 1. Seed Users
    stmt_admin = select(User).where(User.email == "admin@academic.edu")
    if not (await db.execute(stmt_admin)).scalar_one_or_none():
        admin = User(
            email="admin@academic.edu",
            full_name="Academic Administrator",
            department="Dean of Academic Affairs",
            hashed_password=get_password_hash("AdminPassword123!"),
            role="admin",
            is_active=True
        )
        db.add(admin)

    stmt_fac = select(User).where(User.email == "faculty@academic.edu")
    if not (await db.execute(stmt_fac)).scalar_one_or_none():
        faculty = User(
            email="faculty@academic.edu",
            full_name="Dr. Alan Turing",
            department="Computer Science & Engineering",
            hashed_password=get_password_hash("FacultyPassword123!"),
            role="faculty",
            is_active=True
        )
        db.add(faculty)
    
    await db.commit()

    # 2. Seed / Update Courses
    course_id_map = {}
    for c_data in SAMPLE_COURSES:
        stmt_c = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(Course.code == c_data["code"])
        c_inst = (await db.execute(stmt_c)).scalar_one_or_none()
        
        if not c_inst:
            c_inst = Course(
                code=c_data["code"],
                name=c_data["name"],
                department=c_data["department"],
                semester=c_data["semester"],
                academic_year=c_data["academic_year"],
                description=c_data["description"]
            )
            db.add(c_inst)
            await db.flush()

            for u in c_data["units"]:
                unit = Unit(
                    course_id=c_inst.id,
                    unit_number=u["unit_number"],
                    title=u["title"],
                    topics=u["topics"]
                )
                db.add(unit)

            for co in c_data["cos"]:
                co_item = CourseOutcome(
                    course_id=c_inst.id,
                    code=co["code"],
                    description=co["description"],
                    target_bloom_level=co["target_bloom_level"]
                )
                db.add(co_item)
            
            await db.commit()
            await db.refresh(c_inst)
        else:
            # Check if existing units contain generic placeholder text or empty; if so, upgrade to authentic curriculum
            has_generic_units = any(
                "Introduction & Fundamental" in u.title or 
                "Data Representation" in u.title or 
                "Core Algorithms" in u.title
                for u in c_inst.units
            )
            if not c_inst.units or has_generic_units or len(c_inst.course_outcomes) > len(c_data["cos"]):
                c_inst.name = c_data["name"]
                c_inst.department = c_data["department"]
                c_inst.semester = c_data["semester"]
                c_inst.description = c_data["description"]

                for old_u in list(c_inst.units):
                    await db.delete(old_u)
                for old_co in list(c_inst.course_outcomes):
                    await db.delete(old_co)
                await db.flush()

                for u in c_data["units"]:
                    unit = Unit(
                        course_id=c_inst.id,
                        unit_number=u["unit_number"],
                        title=u["title"],
                        topics=u["topics"]
                    )
                    db.add(unit)

                for co in c_data["cos"]:
                    co_item = CourseOutcome(
                        course_id=c_inst.id,
                        code=co["code"],
                        description=co["description"],
                        target_bloom_level=co["target_bloom_level"]
                    )
                    db.add(co_item)
                
                await db.commit()
                await db.refresh(c_inst)

        course_id_map[c_data["code"]] = c_inst.id

    # 3. Seed Sample Textbook Resources & Vector Index
    for r_data in SAMPLE_RESOURCES:
        c_code = r_data["course_code"]
        c_id = course_id_map.get(c_code)
        if not c_id:
            continue

        stmt_r = select(Resource).where(
            Resource.course_id == c_id,
            Resource.file_name == r_data["file_name"]
        )
        existing_r = (await db.execute(stmt_r)).scalar_one_or_none()
        if not existing_r:
            res = Resource(
                course_id=c_id,
                title=r_data["title"],
                file_name=r_data["file_name"],
                file_path=f"./data/uploads/{r_data['file_name']}",
                file_type=r_data["file_type"],
                document_type=r_data["document_type"],
                file_size_bytes=52400,
                status="Processed",
                chunk_count=len(r_data["chunks"])
            )
            db.add(res)
            await db.flush()

            contents = []
            metadatas = []
            doc_ids = []

            for idx, c in enumerate(r_data["chunks"]):
                chunk_obj = ResourceChunk(
                    resource_id=res.id,
                    chunk_index=idx,
                    content=c["content"],
                    page_number=idx * 4 + 1,
                    unit_number=c["unit"],
                    topic=c["topic"],
                    token_count=len(c["content"].split())
                )
                db.add(chunk_obj)

                contents.append(c["content"])
                metadatas.append({
                    "resource_id": res.id,
                    "course_id": c_id,
                    "course_code": c_code,
                    "file_name": r_data["file_name"],
                    "document_type": r_data["document_type"],
                    "unit_number": c["unit"],
                    "page_number": idx * 4 + 1,
                    "topic": c["topic"],
                    "chunk_index": idx
                })
                doc_ids.append(f"res_{res.id}_chunk_{idx}")

            await db.commit()

            # Index to vector store
            await vector_store.add_documents(
                contents=contents,
                metadatas=metadatas,
                doc_ids=doc_ids
            )
