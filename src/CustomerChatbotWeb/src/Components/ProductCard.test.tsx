import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProductCard } from "./ProductCard";
import type { Product } from "../types";

describe("ProductCard", () => {
  const baseProduct: Product = {
    id: "prod-001",
    name: "Wireless Headphones",
    category: "electronics",
    price: 79.99,
    description: "High-quality wireless headphones with noise cancellation",
    attributes: {},
  };

  it("renders product name", () => {
    // Arrange & Act
    render(<ProductCard product={baseProduct} />);

    // Assert
    expect(screen.getByText("Wireless Headphones")).toBeInTheDocument();
  });

  it("renders product price formatted to 2 decimals", () => {
    // Arrange & Act
    render(<ProductCard product={baseProduct} />);

    // Assert
    expect(screen.getByText("$79.99")).toBeInTheDocument();
  });

  it("renders product category", () => {
    // Arrange & Act
    render(<ProductCard product={baseProduct} />);

    // Assert
    expect(screen.getByText("electronics")).toBeInTheDocument();
  });

  it("renders product description", () => {
    // Arrange & Act
    render(<ProductCard product={baseProduct} />);

    // Assert
    expect(
      screen.getByText("High-quality wireless headphones with noise cancellation"),
    ).toBeInTheDocument();
  });

  it("renders image when image_url is provided", () => {
    // Arrange
    const productWithImage: Product = {
      ...baseProduct,
      image_url: "https://example.com/headphones.jpg",
    };

    // Act
    render(<ProductCard product={productWithImage} />);

    // Assert
    const img = screen.getByAltText("Wireless Headphones");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "https://example.com/headphones.jpg");
  });

  it("does not render image when image_url is undefined", () => {
    // Arrange & Act
    render(<ProductCard product={baseProduct} />);

    // Assert
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("formats zero price correctly", () => {
    // Arrange
    const freeProduct: Product = { ...baseProduct, price: 0 };

    // Act
    render(<ProductCard product={freeProduct} />);

    // Assert
    expect(screen.getByText("$0.00")).toBeInTheDocument();
  });
});
