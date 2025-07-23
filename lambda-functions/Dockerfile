# Multi-stage Docker build for AWS Lambda Rust functions

# Build stage
FROM public.ecr.aws/lambda/provided:al2-x86_64 AS builder

# Install dependencies
RUN yum install -y gcc python3 python3-pip
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Install cargo-lambda for building Lambda functions
RUN pip3 install cargo-lambda

# Copy source code
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ src/

# Build each Lambda function
RUN cargo lambda build --release --bin block-fetcher
RUN cargo lambda build --release --bin hash-generator  
RUN cargo lambda build --release --bin stark-prover
RUN cargo lambda build --release --bin stark-verifier

# Production stage for block-fetcher
FROM public.ecr.aws/lambda/provided:al2-x86_64 AS block-fetcher
COPY --from=builder /app/target/lambda/block-fetcher/bootstrap ${LAMBDA_RUNTIME_DIR}
CMD ["block-fetcher"]

# Production stage for hash-generator  
FROM public.ecr.aws/lambda/provided:al2-x86_64 AS hash-generator
COPY --from=builder /app/target/lambda/hash-generator/bootstrap ${LAMBDA_RUNTIME_DIR}
CMD ["hash-generator"]

# Production stage for stark-prover
FROM public.ecr.aws/lambda/provided:al2-x86_64 AS stark-prover
COPY --from=builder /app/target/lambda/stark-prover/bootstrap ${LAMBDA_RUNTIME_DIR}
CMD ["stark-prover"]

# Production stage for stark-verifier
FROM public.ecr.aws/lambda/provided:al2-x86_64 AS stark-verifier
COPY --from=builder /app/target/lambda/stark-verifier/bootstrap ${LAMBDA_RUNTIME_DIR}
CMD ["stark-verifier"]